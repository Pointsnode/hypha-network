#!/usr/bin/env python3
"""
Verify Neural Mesh Installation
Quick sanity check for HYPHA neural components
"""

import sys


def check_imports():
    """Check all required imports"""
    print("Checking imports...")

    try:
        import nacl.signing
        print("  ✅ PyNaCl (Ed25519 signatures)")
    except ImportError:
        print("  ❌ PyNaCl missing - run: pip install pynacl")
        return False

    try:
        import asyncio
        print("  ✅ asyncio (built-in)")
    except ImportError:
        print("  ❌ asyncio missing")
        return False

    try:
        import struct
        import hashlib
        import json
        print("  ✅ Standard library (struct, hashlib, json)")
    except ImportError:
        print("  ❌ Standard library missing")
        return False

    return True


def check_node_modules():
    """Check Node.js and Hyperswarm"""
    import subprocess

    print("\nChecking Node.js environment...")

    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✅ Node.js {version}")
        else:
            print("  ❌ Node.js not working")
            return False
    except FileNotFoundError:
        print("  ❌ Node.js not installed")
        return False
    except Exception as e:
        print(f"  ❌ Node.js check failed: {e}")
        return False

    try:
        result = subprocess.run(
            ['npm', 'list', 'hyperswarm'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if 'hyperswarm@' in result.stdout:
            print("  ✅ Hyperswarm installed")
        else:
            print("  ❌ Hyperswarm missing - run: npm install")
            return False
    except Exception as e:
        print(f"  ⚠️  Hyperswarm check inconclusive: {e}")

    return True


def check_hypha_node():
    """Check hypha_node.py can be imported"""
    print("\nChecking HYPHA Neural Node...")

    try:
        from hypha_node import NeuralNode
        print("  ✅ hypha_node.py importable")

        # Test instantiation
        import hashlib
        seed = hashlib.sha256(b"test").digest()
        node = NeuralNode(seed=seed)
        print(f"  ✅ Node created with ID: {node.node_id.hex()[:16]}")

        return True
    except ImportError as e:
        print(f"  ❌ Cannot import hypha_node: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Node creation failed: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("HYPHA Neural Mesh Verification")
    print("=" * 60)
    print()

    checks = [
        ("Python imports", check_imports),
        ("Node.js environment", check_node_modules),
        ("Neural node", check_hypha_node)
    ]

    results = []

    for name, check_func in checks:
        result = check_func()
        results.append(result)

    print()
    print("=" * 60)

    if all(results):
        print("✅ ALL CHECKS PASSED")
        print()
        print("Ready to run:")
        print("  python3 hypha_node.py")
        print("  python3 test_neural_mesh.py")
        print()
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Fix the issues above before running neural nodes.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
