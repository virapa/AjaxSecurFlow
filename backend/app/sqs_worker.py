import asyncio
import logging
import sys
import os

# Ensure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.modules.ajax.sqs_service import AjaxEventsConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("sqs_worker")

async def main():
    logger.info("Initializing Ajax SQS Consumer Worker...")
    try:
        consumer = AjaxEventsConsumer()
        await consumer.poll()
    except Exception as e:
        logger.critical(f"Worker failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
        sys.exit(0)
