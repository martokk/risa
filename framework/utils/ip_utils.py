import ipaddress
from datetime import UTC, datetime, timedelta

import requests
from fastapi import Request

from app import logger


# Cache for CloudFront IP ranges
_cloudfront_ipv4_ranges: set[ipaddress.IPv4Network] = set()
_cloudfront_ipv6_ranges: set[ipaddress.IPv6Network] = set()
_cloudfront_ranges_last_update: datetime | None = None
_CLOUDFRONT_CACHE_TTL = timedelta(hours=24)  # Update every 24 hours


def _update_cloudfront_ranges() -> None:
    """Update the cached CloudFront IP ranges"""
    global _cloudfront_ipv4_ranges, _cloudfront_ipv6_ranges, _cloudfront_ranges_last_update

    try:
        # Fetch the IP ranges from AWS
        response = requests.get("https://ip-ranges.amazonaws.com/ip-ranges.json", timeout=5)
        response.raise_for_status()
        data = response.json()

        # Extract CloudFront ranges
        new_ipv4_ranges = set()
        new_ipv6_ranges = set()

        for prefix in data.get("prefixes", []):
            if prefix.get("service") == "CLOUDFRONT":
                try:
                    new_ipv4_ranges.add(ipaddress.IPv4Network(prefix["ip_prefix"]))
                except ValueError:
                    logger.warning(f"Invalid IPv4 prefix: {prefix['ip_prefix']}")

        for prefix in data.get("ipv6_prefixes", []):
            if prefix.get("service") == "CLOUDFRONT":
                try:
                    new_ipv6_ranges.add(ipaddress.IPv6Network(prefix["ipv6_prefix"]))
                except ValueError:
                    logger.warning(f"Invalid IPv6 prefix: {prefix['ipv6_prefix']}")

        # Update the cache
        _cloudfront_ipv4_ranges = new_ipv4_ranges
        _cloudfront_ipv6_ranges = new_ipv6_ranges
        _cloudfront_ranges_last_update = datetime.now(UTC)
        logger.info(
            f"Updated CloudFront IP ranges:{len(new_ipv4_ranges)} IPv4, {len(new_ipv6_ranges)} IPv6"
        )

    except Exception as e:
        logger.error(f"Error updating CloudFront IP ranges: {str(e)}")


def is_cloudfront_ip(ip: str) -> bool:
    """Check if an IP address is from CloudFront"""
    global _cloudfront_ranges_last_update

    # Update ranges if needed
    if (
        _cloudfront_ranges_last_update is None
        or datetime.now(UTC) - _cloudfront_ranges_last_update > _CLOUDFRONT_CACHE_TTL
    ):
        _update_cloudfront_ranges()

    try:
        # Parse the IP address
        ip_obj = ipaddress.ip_address(ip)

        # Check against appropriate ranges
        if isinstance(ip_obj, ipaddress.IPv4Address):
            return any(ip_obj in network for network in _cloudfront_ipv4_ranges)

        return any(ip_obj in network for network in _cloudfront_ipv6_ranges)
    except ValueError:
        logger.warning(f"Invalid IP address: {ip}")
        return False


def get_client_ips(forwarded_header: str | None, direct_ip: str) -> list[str]:
    """
    Extract all unique IP addresses from the X-Forwarded-For header.
    With CloudFront, the first IP is always the real client IP.
    Returns a list containing only the real client IP.

    Args:
        forwarded_header: The X-Forwarded-For header value
        direct_ip: The direct client IP address

    Returns:
        list[str]: List containing only the real client IP
    """
    if not forwarded_header:
        return [direct_ip]

    # With CloudFront, first IP is always the real client IP
    ips = [ip.strip() for ip in forwarded_header.split(",")]
    return [ips[0]]  # Return only the first IP


def get_real_ip(forwarded_header: str | None, direct_ip: str) -> str:
    """
    Get the real client IP address, which is the first IP in X-Forwarded-For.
    If no forwarded header is present, returns the direct IP.

    Args:
        forwarded_header: The X-Forwarded-For header value
        direct_ip: The direct client IP address

    Returns:
        str: The real client IP address
    """
    ips = get_client_ips(forwarded_header, direct_ip)
    return ips[0]  # First IP is the original client


def get_ip(request: Request) -> str:
    """Get the real client IP address"""
    return get_real_ip(
        request.headers.get("X-Forwarded-For"), request.client.host if request.client else ""
    )


def get_ips(request: Request) -> list[str]:
    """Get the real client IP (ignoring CloudFront IPs)"""
    return get_client_ips(
        request.headers.get("X-Forwarded-For"), request.client.host if request.client else ""
    )
