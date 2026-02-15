"""
Input validation for HYPHA SDK

Provides comprehensive validation for all user inputs to prevent
security vulnerabilities and improve error messages.
"""

import re
from web3 import Web3


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


def validate_ethereum_address(address: str, param_name: str = "address") -> str:
    """
    Validate and checksum Ethereum address

    Args:
        address: Ethereum address to validate
        param_name: Parameter name for error messages

    Returns:
        Checksummed Ethereum address

    Raises:
        ValidationError: If address is invalid
    """
    if not isinstance(address, str):
        raise ValidationError(f"{param_name} must be string, got {type(address).__name__}")

    if not address.startswith('0x'):
        raise ValidationError(f"{param_name} must start with '0x'")

    if len(address) != 42:
        raise ValidationError(f"{param_name} must be 42 characters (0x + 40 hex), got {len(address)}")

    if not re.match(r'^0x[0-9a-fA-F]{40}$', address):
        raise ValidationError(f"{param_name} contains invalid characters")

    try:
        return Web3.to_checksum_address(address)
    except ValueError as e:
        raise ValidationError(f"{param_name} has invalid checksum") from e


def validate_amount(amount, param_name: str = "amount", min_value: float = 0.0, max_value: float = 1_000_000_000.0) -> float:
    """
    Validate payment amount

    Args:
        amount: Amount to validate
        param_name: Parameter name for error messages
        min_value: Minimum allowed value (exclusive)
        max_value: Maximum allowed value (inclusive)

    Returns:
        Validated amount as float

    Raises:
        ValidationError: If amount is invalid
    """
    if not isinstance(amount, (int, float)):
        raise ValidationError(f"{param_name} must be number, got {type(amount).__name__}")

    if amount <= min_value:
        raise ValidationError(f"{param_name} must be greater than {min_value}")

    if amount > max_value:
        raise ValidationError(f"{param_name} exceeds maximum of {max_value}")

    return float(amount)


def validate_private_key(key: str) -> str:
    """
    Validate private key format

    Args:
        key: Private key to validate (with or without 0x prefix)

    Returns:
        Private key with 0x prefix

    Raises:
        ValidationError: If private key is invalid
    """
    if not isinstance(key, str):
        raise ValidationError(f"Private key must be string, got {type(key).__name__}")

    # Remove 0x prefix if present
    k = key.replace('0x', '').replace('0X', '')

    if len(k) != 64:
        raise ValidationError(f"Private key must be 64 hex characters, got {len(k)}")

    if not re.match(r'^[0-9a-fA-F]{64}$', k):
        raise ValidationError("Private key contains invalid characters")

    if k == '0' * 64:
        raise ValidationError("Private key cannot be all zeros")

    return '0x' + k


def validate_escrow_id(escrow_id: str, param_name: str = "escrow_id") -> str:
    """
    Validate escrow ID (bytes32)

    Args:
        escrow_id: Escrow ID to validate (with or without 0x prefix)
        param_name: Parameter name for error messages

    Returns:
        Escrow ID with 0x prefix

    Raises:
        ValidationError: If escrow ID is invalid
    """
    if not isinstance(escrow_id, str):
        raise ValidationError(f"{param_name} must be string, got {type(escrow_id).__name__}")

    # Remove 0x prefix if present
    eid = escrow_id.replace('0x', '').replace('0X', '')

    if len(eid) != 64:
        raise ValidationError(f"{param_name} must be 64 hex characters (bytes32), got {len(eid)}")

    if not re.match(r'^[0-9a-fA-F]{64}$', eid):
        raise ValidationError(f"{param_name} contains invalid characters")

    return '0x' + eid


def validate_task_description(task: str, param_name: str = "task", max_length: int = 10000) -> str:
    """
    Validate task description

    Args:
        task: Task description to validate
        param_name: Parameter name for error messages
        max_length: Maximum allowed length

    Returns:
        Validated task description

    Raises:
        ValidationError: If task description is invalid
    """
    if not isinstance(task, str):
        raise ValidationError(f"{param_name} must be string, got {type(task).__name__}")

    if len(task) == 0:
        raise ValidationError(f"{param_name} cannot be empty")

    if len(task) > max_length:
        raise ValidationError(f"{param_name} too long (max {max_length} characters)")

    return task


def validate_deadline_hours(hours, param_name: str = "deadline_hours") -> int:
    """
    Validate deadline hours

    Args:
        hours: Number of hours for deadline
        param_name: Parameter name for error messages

    Returns:
        Validated hours as integer

    Raises:
        ValidationError: If hours is invalid
    """
    if not isinstance(hours, (int, float)):
        raise ValidationError(f"{param_name} must be number, got {type(hours).__name__}")

    if hours <= 0:
        raise ValidationError(f"{param_name} must be greater than 0")

    if hours > 8760:  # 1 year
        raise ValidationError(f"{param_name} exceeds maximum of 8760 hours (1 year)")

    return int(hours)


def validate_seed(seed: str) -> str:
    """
    Validate seed for key generation

    Args:
        seed: Seed string to validate

    Returns:
        Validated seed

    Raises:
        ValidationError: If seed is invalid
    """
    if not isinstance(seed, str):
        raise ValidationError(f"Seed must be string, got {type(seed).__name__}")

    if len(seed) < 8:
        raise ValidationError("Seed must be at least 8 characters for security")

    if len(seed) > 1000:
        raise ValidationError("Seed too long (max 1000 characters)")

    return seed
