"""
Learning Assistant - A modular AI learning CLI tool platform.

This package provides a plugin-based architecture for various learning modules
including video summary, link learning, and vocabulary management.
"""

__version__ = "0.1.0"
__author__ = "Learning Assistant Team"

from learning_assistant.cli import app
from learning_assistant.core.plugin_manager import PluginManager

__all__ = ["__version__", "__author__", "app", "PluginManager"]
