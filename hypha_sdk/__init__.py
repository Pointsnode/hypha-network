"""HYPHA SDK - P2P Infrastructure for Autonomous AI Agents"""

from .core import Agent
from .seed_manager import SeedManager
from .wallet_wdk import Wallet
from .protocol import Message, MessageType
from .discovery import Discovery
from .validation import ValidationError

__version__ = "0.2.0"
__all__ = ["Agent", "SeedManager", "Wallet", "Discovery", "Message", "MessageType", "ValidationError"]
