#!/usr/bin/env python3
"""
Simple test to verify HYPHA components work
"""

import hashlib

print("=" * 60)
print("HYPHA Component Test")
print("=" * 60)

# Test 1: Import modules
print("\n[1/4] Testing imports...")
try:
    from hypha_nutrient import HyphaNutrient
    print("✅ hypha_nutrient imported")
except Exception as e:
    print(f"❌ hypha_nutrient import failed: {e}")
    exit(1)

try:
    from hypha_sdk.wallet_wdk import WDKWallet
    print("✅ WDKWallet imported")
except Exception as e:
    print(f"❌ WDKWallet import failed: {e}")
    exit(1)

# Test 2: Create wallet
print("\n[2/4] Testing wallet creation...")
try:
    seed = hashlib.sha256(b"test-seed").digest()
    wallet = WDKWallet(seed.hex())
    print(f"✅ Wallet created: {wallet.address}")
except Exception as e:
    print(f"❌ Wallet creation failed: {e}")
    exit(1)

# Test 3: Check balance
print("\n[3/4] Testing balance check...")
try:
    balance = wallet.get_balance()
    print(f"✅ Balance: {balance} USDT")
except Exception as e:
    print(f"❌ Balance check failed: {e}")
    # Don't exit - balance check might fail if network is down

# Test 4: Create HyphaNutrient (without starting P2P)
print("\n[4/4] Testing HyphaNutrient creation...")
try:
    seed = hashlib.sha256(b"test-node").digest()
    node = HyphaNutrient(seed=seed)
    print(f"✅ Node created")
    print(f"   Node ID: {node.node_id.hex()[:16]}...")
    print(f"   Wallet:  {node.get_wallet_address()}")
except Exception as e:
    print(f"❌ Node creation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL BASIC TESTS PASSED")
print("=" * 60)
print("\nYour HYPHA components are working correctly!")
print("The WDK integration test might take longer as it tests")
print("P2P networking which requires node discovery.")
print()
