import asyncio
import logging
import sys
from pathlib import Path

# --------------------------------------------------
# Package bootstrap (THIS IS THE FIX)
# --------------------------------------------------

# Allow running as a script: python main.py
if __package__ is None or __package__ == "":
    # Add parent directory to sys.path
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    sys.path.insert(0, str(parent_dir))
    __package__ = current_dir.name

# Now relative imports will work
from .assistant import MikaAssistant
from .config import Config
from .utils import logger

# --------------------------------------------------
# Main logic
# --------------------------------------------------


async def main():
    logger.info("Starting MIKA Assistant...")

    # Load configuration
    config_path = Path(__file__).parent / "config.json"
    config = Config.load_from_file(config_path)

    # Initialize Assistant
    assistant = MikaAssistant(config)

    # Register signal handlers (async-safe)
    assistant.register_signal_handlers()

    try:
        await assistant.start()
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        await assistant.shutdown()


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Force exit.")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)
