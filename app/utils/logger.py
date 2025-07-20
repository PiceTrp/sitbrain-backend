import logging
import os
from enum import StrEnum

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

LOG_FORMAT_DEBUG = (
    "%(asctime)s:%(levelname)s:%(message)s:%(filename)s:%(funcName)s:%(lineno)d"
)


class LogLevel(StrEnum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"


# Set up basic configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all types of logs
    format=LOG_FORMAT_DEBUG,
    handlers=[
        logging.FileHandler("logs/app.log"),  # Logs to a file
        logging.StreamHandler(),  # Logs to console
    ],
)

# Create a custom logger for your module
LOGGER = logging.getLogger("app")
