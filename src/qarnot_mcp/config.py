"""Configuration for Qarnot MCP Server."""

import os
from dotenv import load_dotenv

load_dotenv()

QARNOT_BASE_URL = os.getenv("QARNOT_BASE_URL", "https://api.qarnot.com")
QARNOT_API_VERSION = os.getenv("QARNOT_API_VERSION", "1")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
