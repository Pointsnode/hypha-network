#!/usr/bin/env python3
"""
HYPHA Installation Verification Script

Run this script to verify that HYPHA is properly installed and configured.
"""

import sys
import os
from typing import List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """Check Python version >= 3.8"""
    if sys.version_info < (3, 8):
        return False, f"Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.8+)"
    return True, f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def check_imports() -> List[Tuple[bool, str]]:
    """Check all required imports"""
    results = []

    # Core dependencies
    imports = [
        ("web3", "Web3"),
        ("nacl", "PyNaCl"),
        ("dotenv", "python-dotenv"),
        ("pytest", "pytest"),
    ]

    for module, name in imports:
        try:
            __import__(module)
            results.append((True, f"{name} installed"))
        except ImportError:
            results.append((False, f"{name} NOT installed"))

    return results

def check_hypha_sdk() -> Tuple[bool, str]:
    """Check HYPHA SDK can be imported"""
    try:
        from hypha_sdk import Agent
        return True, "hypha_sdk.Agent imported successfully"
    except ImportError as e:
        return False, f"hypha_sdk import failed: {e}"

def check_validation() -> Tuple[bool, str]:
    """Check validation module"""
    try:
        from hypha_sdk.validation import validate_ethereum_address, ValidationError

        # Test validation
        try:
            validate_ethereum_address("invalid")
            return False, "Validation should have failed for invalid address"
        except ValidationError:
            return True, "Validation module working correctly"
    except ImportError as e:
        return False, f"Validation import failed: {e}"

def check_health_module() -> Tuple[bool, str]:
    """Check health module"""
    try:
        from hypha_sdk.health import HealthCheck
        return True, "Health check module available"
    except ImportError as e:
        return False, f"Health module import failed: {e}"

def check_config() -> Tuple[bool, str]:
    """Check configuration module"""
    try:
        from hypha_sdk.config import Config
        config = Config()

        if config.is_fully_configured():
            return True, "Fully configured (all env vars set)"
        else:
            missing = config.get_missing_config()
            return True, f"Partially configured (missing: {', '.join(missing)})"
    except Exception as e:
        return False, f"Config check failed: {e}"

def check_node_js() -> Tuple[bool, str]:
    """Check Node.js installation"""
    try:
        import subprocess
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Node.js {version}"
        else:
            return False, "Node.js not responding"
    except FileNotFoundError:
        return False, "Node.js NOT installed"
    except Exception as e:
        return False, f"Node.js check failed: {e}"

def check_npm_packages() -> Tuple[bool, str]:
    """Check npm packages"""
    try:
        import subprocess
        result = subprocess.run(
            ['npm', 'list', 'hyperswarm'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if 'hyperswarm@' in result.stdout:
            return True, "npm packages installed (hyperswarm found)"
        else:
            return False, "npm packages NOT installed (run: npm install)"
    except FileNotFoundError:
        return False, "npm NOT installed"
    except Exception as e:
        return False, f"npm check failed: {e}"

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("HYPHA Installation Verification")
    print("=" * 60)
    print()

    all_passed = True

    # Python version
    passed, msg = check_python_version()
    print(f"{'✅' if passed else '❌'} {msg}")
    all_passed = all_passed and passed
    print()

    # Python dependencies
    print("Python Dependencies:")
    for passed, msg in check_imports():
        print(f"  {'✅' if passed else '❌'} {msg}")
        all_passed = all_passed and passed
    print()

    # HYPHA SDK
    passed, msg = check_hypha_sdk()
    print(f"{'✅' if passed else '❌'} {msg}")
    all_passed = all_passed and passed
    print()

    # Validation module
    passed, msg = check_validation()
    print(f"{'✅' if passed else '❌'} {msg}")
    all_passed = all_passed and passed
    print()

    # Health module
    passed, msg = check_health_module()
    print(f"{'✅' if passed else '❌'} {msg}")
    all_passed = all_passed and passed
    print()

    # Configuration
    passed, msg = check_config()
    print(f"{'✅' if passed else '⚠️ '} {msg}")
    # Don't fail on partial config
    print()

    # Node.js
    passed, msg = check_node_js()
    print(f"{'✅' if passed else '❌'} {msg}")
    all_passed = all_passed and passed
    print()

    # npm packages
    passed, msg = check_npm_packages()
    print(f"{'✅' if passed else '❌'} {msg}")
    all_passed = all_passed and passed
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print()
        print("Next steps:")
        print("1. Configure .env file with your credentials")
        print("2. Deploy contracts: npm run deploy:testnet")
        print("3. Run health check: see docs/DEPLOYMENT_GUIDE.md")
        print("4. Try examples: python examples/three_lines.py")
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please fix the failed checks above.")
        print("See README.md for installation instructions.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
