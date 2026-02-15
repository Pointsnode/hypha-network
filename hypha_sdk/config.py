"""
Configuration management for HYPHA SDK

Centralizes environment variable loading and validation
"""

import os
from dotenv import load_dotenv
from .validation import validate_ethereum_address, validate_private_key, ValidationError
from .logging_config import logger

# Load environment variables
load_dotenv()


class Config:
    """HYPHA configuration from environment variables"""

    def __init__(self):
        """Initialize configuration from environment"""

        # Private key (optional)
        self.private_key = os.getenv('PRIVATE_KEY')
        if self.private_key:
            try:
                self.private_key = validate_private_key(self.private_key)
                logger.debug("PRIVATE_KEY validated successfully")
            except ValidationError as e:
                logger.error(f"Invalid PRIVATE_KEY in .env: {e}")
                raise ValueError(f"Invalid PRIVATE_KEY: {e}") from e

        # Escrow contract address (optional)
        self.escrow_address = os.getenv('ESCROW_CONTRACT_ADDRESS')
        if self.escrow_address:
            try:
                self.escrow_address = validate_ethereum_address(
                    self.escrow_address,
                    "ESCROW_CONTRACT_ADDRESS"
                )
                logger.debug(f"ESCROW_CONTRACT_ADDRESS: {self.escrow_address}")
            except ValidationError as e:
                logger.error(f"Invalid ESCROW_CONTRACT_ADDRESS in .env: {e}")
                raise ValueError(f"Invalid ESCROW_CONTRACT_ADDRESS: {e}") from e

        # USDT contract address (optional)
        self.usdt_address = os.getenv('USDT_CONTRACT_ADDRESS')
        if self.usdt_address:
            try:
                self.usdt_address = validate_ethereum_address(
                    self.usdt_address,
                    "USDT_CONTRACT_ADDRESS"
                )
                logger.debug(f"USDT_CONTRACT_ADDRESS: {self.usdt_address}")
            except ValidationError as e:
                logger.error(f"Invalid USDT_CONTRACT_ADDRESS in .env: {e}")
                raise ValueError(f"Invalid USDT_CONTRACT_ADDRESS: {e}") from e

        # Web3 provider URI
        self.web3_provider = os.getenv('WEB3_PROVIDER_URI', 'https://sepolia.base.org')
        logger.debug(f"WEB3_PROVIDER_URI: {self.web3_provider}")

        # Log level
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

        # P2P topic
        self.default_topic = os.getenv('HYPHA_DEFAULT_TOPIC', 'hypha-agents')

    def is_fully_configured(self) -> bool:
        """Check if all required configuration is present"""
        return all([
            self.private_key,
            self.escrow_address,
            self.usdt_address,
            self.web3_provider
        ])

    def get_missing_config(self) -> list:
        """Get list of missing configuration keys"""
        missing = []
        if not self.private_key:
            missing.append('PRIVATE_KEY')
        if not self.escrow_address:
            missing.append('ESCROW_CONTRACT_ADDRESS')
        if not self.usdt_address:
            missing.append('USDT_CONTRACT_ADDRESS')
        return missing

    def validate_all(self):
        """Validate all configuration"""
        errors = []

        if self.private_key:
            try:
                validate_private_key(self.private_key)
            except ValidationError as e:
                errors.append(f"PRIVATE_KEY: {e}")

        if self.escrow_address:
            try:
                validate_ethereum_address(self.escrow_address, "ESCROW_CONTRACT_ADDRESS")
            except ValidationError as e:
                errors.append(f"ESCROW_CONTRACT_ADDRESS: {e}")

        if self.usdt_address:
            try:
                validate_ethereum_address(self.usdt_address, "USDT_CONTRACT_ADDRESS")
            except ValidationError as e:
                errors.append(f"USDT_CONTRACT_ADDRESS: {e}")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

        logger.info("Configuration validated successfully")

    def __repr__(self) -> str:
        """String representation (hides sensitive data)"""
        return (
            f"Config(\n"
            f"  private_key={'*' * 10 if self.private_key else 'Not set'},\n"
            f"  escrow_address={self.escrow_address or 'Not set'},\n"
            f"  usdt_address={self.usdt_address or 'Not set'},\n"
            f"  web3_provider={self.web3_provider},\n"
            f"  log_level={self.log_level}\n"
            f")"
        )


# Global config instance
config = Config()
