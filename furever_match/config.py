"""
Configuration module for the app
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""

    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DEBUG = True


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv("FLASK_ENV", "development")

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    return config_map.get(env, DevelopmentConfig)
