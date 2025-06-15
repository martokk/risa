import bleach


def sanitize_html(content: str) -> str:
    """Sanitize HTML content"""
    allowed_tags = [
        "p",
        "br",
        "strong",
        "em",
        "u",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "a",
        "img",
    ]
    allowed_attrs = {"a": ["href", "title"], "img": ["src", "alt", "title"]}
    return str(bleach.clean(content, tags=allowed_tags, attributes=allowed_attrs, strip=True))
