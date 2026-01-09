import logging
import logging.handlers
from functools import wraps
from pathlib import Path

# ---------------------------
# Logger Setup
# ---------------------------
LOG_FILE = Path("mika_new.log")
LOG_DIR = LOG_FILE.parent

# Ensure log directory exists
if LOG_DIR and not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            filename=str(LOG_FILE),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        ),
        logging.StreamHandler()  # Output to console
    ]
)

logger = logging.getLogger(__name__)

# Test log to verify configuration
logger.info("Logging configuration initialized successfully")


# ---------------------------
# Exception Handling
# ---------------------------
def handle_exceptions(func):
    """
    Decorator for centralized exception handling in async functions.
    Logs the error and prevents crashes.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper
