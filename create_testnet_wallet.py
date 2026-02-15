#!/usr/bin/env python3
"""
Create a new testnet wallet and add it to .env automatically
"""

import secrets
import sys
import os

def create_wallet():
    """Generate new Ethereum wallet"""
    try:
        from eth_account import Account
    except ImportError:
        print("Installing eth-account package...")
        os.system("python3 -m pip install --user eth-account")
        from eth_account import Account

    # Generate random private key
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)

    return {
        'address': account.address,
        'private_key': private_key
    }


def update_env_file(private_key):
    """Update .env file with new private key"""
    env_path = ".env"

    if not os.path.exists(env_path):
        print(f"❌ Error: {env_path} not found")
        return False

    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update private key line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('PRIVATE_KEY='):
            lines[i] = f'PRIVATE_KEY={private_key}\n'
            updated = True
            break

    if not updated:
        print("❌ Error: PRIVATE_KEY line not found in .env")
        return False

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)

    return True


def main():
    print("=" * 70)
    print("HYPHA Testnet Wallet Generator")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT: This creates a TESTNET wallet for Base Sepolia only!")
    print("   NEVER use this wallet for mainnet or real funds!")
    print()

    response = input("Create a new testnet wallet? (y/n): ").lower().strip()

    if response != 'y':
        print("\nCancelled.")
        return 0

    print()
    print("Generating new wallet...")

    wallet = create_wallet()

    print()
    print("=" * 70)
    print("✅ NEW TESTNET WALLET CREATED")
    print("=" * 70)
    print()
    print(f"Address:     {wallet['address']}")
    print(f"Private Key: {wallet['private_key']}")
    print()
    print("⚠️  SAVE THIS INFORMATION!")
    print()
    print("Wallet Address: You'll need this to get testnet funds")
    print("Private Key:    Will be added to .env automatically")
    print("=" * 70)
    print()

    # Ask if they want to update .env
    response = input("Add this private key to .env automatically? (y/n): ").lower().strip()

    if response == 'y':
        if update_env_file(wallet['private_key']):
            print()
            print("✅ Successfully updated .env file!")
            print()
            print("Next steps:")
            print()
            print("1. ✅ Private key added to .env")
            print()
            print("2. Get testnet ETH from faucet:")
            print("   https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet")
            print(f"   Enter this address: {wallet['address']}")
            print()
            print("3. Wait for transaction to confirm (~30 seconds)")
            print()
            print("4. Verify setup:")
            print("   python3 verify_setup.py")
            print()
            print("5. Deploy:")
            print("   ./quick_deploy.sh")
            print()
        else:
            print()
            print("❌ Failed to update .env file")
            print()
            print("Add it manually:")
            print("  nano .env")
            print(f"  Replace PRIVATE_KEY line with: PRIVATE_KEY={wallet['private_key']}")
            print()
    else:
        print()
        print("To add it manually later:")
        print()
        print("1. Edit .env file:")
        print("   nano .env")
        print()
        print("2. Find this line:")
        print("   PRIVATE_KEY=your_private_key_here")
        print()
        print("3. Replace with:")
        print(f"   PRIVATE_KEY={wallet['private_key']}")
        print()
        print("4. Save (Ctrl+X, Y, Enter)")
        print()

    print("=" * 70)
    print("📋 SAVE THESE FOR YOUR RECORDS:")
    print("=" * 70)
    print(f"Wallet Address: {wallet['address']}")
    print(f"Private Key:    {wallet['private_key']}")
    print("Network:        Base Sepolia Testnet")
    print("Chain ID:       84532")
    print("RPC URL:        https://sepolia.base.org")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
