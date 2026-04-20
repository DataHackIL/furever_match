"""
Tests for the main module
"""

import pytest
from furever_match.main import App


def test_app_initialization():
    """Test App initialization"""
    app = App()
    assert app is not None
    assert isinstance(app.config, dict)


def test_app_run():
    """Test App run method"""
    app = App()
    # This should not raise an exception
    app.run()
