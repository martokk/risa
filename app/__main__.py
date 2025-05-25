from app import logger
from app.core.server import start_server


def main() -> None:
    logger.info("\n")
    logger.info("--- Start ---")
    logger.info("Starting Server...")
    start_server()


if __name__ == "__main__":
    main()  # pragma: no cover
