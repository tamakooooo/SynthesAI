"""
SynthesAI - Synthesize Knowledge with AI Intelligence.

SynthesAI is an AI-powered learning assistant that synthesizes knowledge from
videos, articles, and text into structured learning materials.

From Complexity to Clarity.
"""

__version__ = "0.3.1"
__author__ = "SynthesAI Team"
__package__ = "synthesai"

from learning_assistant.cli import app
from learning_assistant.core.plugin_manager import PluginManager

__all__ = ["__version__", "__author__", "__package__", "app", "PluginManager"]
