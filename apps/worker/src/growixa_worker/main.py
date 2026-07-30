import asyncio
import logging

from growixa_worker.config import get_settings
from growixa_worker.consumer import consume_forever


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    asyncio.run(consume_forever(settings.rabbitmq_url))


if __name__ == "__main__":
    main()
