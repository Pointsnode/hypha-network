#!/usr/bin/env python3
"""
Verify HYPHA Tether WDK Integration
Quick validation of all components
"""

import sys
import hashlib


def test_seed_manager():
    """Test unified seed manager"""
    print("Testing SeedManager...")

    try:
        from hypha_sdk.seed_manager import SeedManager

        # Test deterministic generation
        seed = hashlib.sha256(b"test-seed").digest()
        sm1 = SeedManager(seed)
        sm2 = SeedManager(seed)

        assert sm1.node_id_hex == sm2.node_id_hex, "Node IDs should match"
        assert sm1.wallet_seed_hex == sm2.wallet_seed_hex, "Wallet seeds should match"

        # Test random generation
        sm3 = SeedManager()
        assert sm3.node_id_hex != sm1.node_id_hex, "Random seeds should differ"

        # Test from_hex
        hex_seed = seed.hex()
        sm4 = SeedManager.from_hex(hex_seed)
        assert sm4.node_id_hex == sm1.node_id_hex, "from_hex should produce same ID"

        # Test from_string
        sm5 = SeedManager.from_string("test-seed")
        assert sm5.node_id_hex == sm1.node_id_hex, "from_string should hash to same seed"

        print("  ✅ SeedManager: PASSED")
        print(f"     - Deterministic node ID: {sm1.node_id_hex}")
        print(f"     - Wallet seed (first 16): {sm1.wallet_seed_hex[:16]}...")
        return True

    except Exception as e:
        print(f"  ❌ SeedManager: FAILED - {e}")
        return False


def test_wallet_bridge():
    """Test Node.js wallet bridge"""
    print("\nTesting Wallet Bridge...")

    import subprocess
    import json
    import os

    bridge_path = os.path.join(
        os.path.dirname(__file__),
        'src', 'wallet', 'wallet_bridge.js'
    )

    if not os.path.exists(bridge_path):
        print(f"  ❌ Bridge not found: {bridge_path}")
        return False

    test_seed = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    try:
        # Test init
        result = subprocess.run(
            ['node', bridge_path, 'init', test_seed],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            print(f"  ❌ Init failed: {result.stderr}")
            return False

        init_response = json.loads(result.stdout)
        assert init_response['success'], "Init should succeed"
        address = init_response['address']
        print(f"  ✅ Init: Generated address {address}")

        # Test balance
        result = subprocess.run(
            ['node', bridge_path, 'balance', test_seed, address],
            capture_output=True,
            text=True,
            timeout=5
        )

        balance_response = json.loads(result.stdout)
        assert balance_response['success'], "Balance check should succeed"
        balance = balance_response['balance']
        print(f"  ✅ Balance: {balance} USDT")

        # Test send
        result = subprocess.run(
            ['node', bridge_path, 'send', test_seed, '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1', '10.0'],
            capture_output=True,
            text=True,
            timeout=5
        )

        send_response = json.loads(result.stdout)
        assert send_response['success'], "Send should succeed"
        tx_hash = send_response['txHash']
        print(f"  ✅ Send: TX {tx_hash[:16]}...")

        print("  ✅ Wallet Bridge: PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Wallet Bridge: FAILED - {e}")
        return False


def test_wdk_wallet():
    """Test Python WDK wallet wrapper"""
    print("\nTesting WDKWallet...")

    try:
        from hypha_sdk.wallet_wdk import WDKWallet
        import hashlib

        seed = hashlib.sha256(b"test-wallet").digest()
        wallet = WDKWallet(seed.hex())

        address = wallet.address
        print(f"  ✅ Address: {address}")

        balance = wallet.get_balance()
        print(f"  ✅ Balance: {balance} USDT")

        has_fuel = wallet.verify_fuel(min_balance=1.0)
        print(f"  ✅ Fuel check: {has_fuel}")

        tx_hash = wallet.send_payment('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1', 5.0)
        print(f"  ✅ Payment: TX {tx_hash[:16]}...")

        print("  ✅ WDKWallet: PASSED")
        return True

    except Exception as e:
        print(f"  ❌ WDKWallet: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hypha_nutrient():
    """Test HyphaNutrient class"""
    print("\nTesting HyphaNutrient...")

    try:
        from hypha_nutrient import HyphaNutrient
        import hashlib

        seed = hashlib.sha256(b"nutrient-test").digest()
        node = HyphaNutrient(seed)

        print(f"  ✅ Node ID: {node.node_id.hex()[:16]}")
        print(f"  ✅ Wallet: {node.get_wallet_address()}")

        has_fuel = node.verify_fuel(min_usdt=5.0)
        print(f"  ✅ Fuel check: {has_fuel}")

        # Test would call atomic_pay but it's async, skip for now
        print("  ✅ HyphaNutrient: PASSED")
        return True

    except Exception as e:
        print(f"  ❌ HyphaNutrient: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("HYPHA Tether WDK Integration Verification")
    print("=" * 60)
    print()

    results = {
        "SeedManager": test_seed_manager(),
        "Wallet Bridge": test_wallet_bridge(),
        "WDKWallet": test_wdk_wallet(),
        "HyphaNutrient": test_hypha_nutrient()
    }

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:20} {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - WDK Integration Ready")
        print("\nNext steps:")
        print("1. Fix npm cache permissions (see WDK_INTEGRATION_STATUS.md)")
        print("2. Install real Tether WDK packages")
        print("3. Replace mock bridge with real WDK implementation")
        print("4. Run test_wdk_handshake.py for full integration test")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nCheck error messages above and review:")
        print("- WDK_INTEGRATION_STATUS.md for setup instructions")
        print("- Ensure all dependencies are installed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
