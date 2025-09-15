"""
OpenAI Client Utility
Centralized configuration for OpenAI client with ChatAnywhere API
"""
import os
from openai import OpenAI

# Initialize OpenAI client with ChatAnywhere API configuration
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_openai_client():
    """
    Get the configured OpenAI client instance
    
    Returns:
        OpenAI: Configured OpenAI client with ChatAnywhere API settings
    """
    return client
