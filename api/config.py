"""
Configuration settings for the API.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Soniox API configuration (used for transcription throughout the system)
# Set SONIOX_API_KEY in your environment or .env file.
SONIOX_API_KEY = os.getenv("SONIOX_API_KEY")

# Base URL for Soniox speech-to-text API.
SONIOX_API_BASE_URL = os.getenv("SONIOX_API_BASE_URL", "https://api.soniox.com")

# Default Soniox model to use for async STT.
# "stt-async-v3" is Soniox's current recommended async model family.
SONIOX_MODEL_ID = os.getenv("SONIOX_MODEL_ID", "stt-async-v3")

# Azure OpenAI API configuration
AZURE_KEY = os.getenv("AZURE_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://demo-kyc.openai.azure.com/openai/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to gpt-4o-mini for cost efficiency

# For backward compatibility, also check OPENAI_API_KEY
OPENAI_API_KEY = AZURE_KEY or os.getenv("OPENAI_API_KEY")

