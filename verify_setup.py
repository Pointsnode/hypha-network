#!/usr/bin/env python3
"""
Quick setup verification for HYPHA Beta Launch
"""

import sys
import os

def check_env_file():
    """Check if .env file exists and has required keys"""
    print("Checking .env file...")

    env_path = ".env"
    if not os.path.exists(env_path):
        print("  ❌ .env file not found")
        return False

    with open(env_path) as f:
        content = f.read()

    required = {
        "WEB3_PROVIDER_URI": "https://sepolia.base.org",
        "USDT_CONTRACT_ADDRESS": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    }

    missing = []
    for key, expected in required.items():
        if expected not in content:
            missing.append(f"{key}={expected}")

    if missing:
        print(f"  ⚠️  Missing/incorrect: {', '.join(missing)}")

    has_key = "PRIVATE_KEY=" in content and "your_private_key_here" not in content

    if has_key:
        print("  ✅ .env file configured")
        return True
    else:
        print("  ⚠️  .env exists but PRIVATE_KEY not set")
        return False


def check_python_packages():
    """Check if required Python packages are installed"""
    print("\nChecking Python packages...")

    packages = ["web3", "nacl", "pytest"]
    missing = []

    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} not found")
            missing.append(pkg)

    return len(missing) == 0


def check_nodejs_packages():
    """Check if required Node.js packages are installed"""
    print("\nChecking Node.js packages...")

    import subprocess

    try:
        result = subprocess.run(
            ["npm", "list", "--depth=0"],
            capture_output=True,
            text=True,
            timeout=10
        )

        packages = {
            "@tetherto/wdk": False,
            "@tetherto/wdk-wallet-evm": False,
            "ethers": False,
            "hyperswarm": False
        }

        for pkg in packages:
            if pkg in result.stdout:
                packages[pkg] = True
                print(f"  ✅ {pkg}")
            else:
                print(f"  ❌ {pkg} not found")

        return all(packages.values())

    except Exception as e:
        print(f"  ❌ Error checking npm packages: {e}")
        return False


def check_wallet_bridge():
    """Check if WDK wallet bridge exists and works"""
    print("\nChecking WDK wallet bridge...")

    bridge_path = "src/wallet/wallet_bridge.js"
    if not os.path.exists(bridge_path):
        print(f"  ❌ {bridge_path} not found")
        return False

    print(f"  ✅ Wallet bridge exists")

    # Try to run it
    import subprocess
    try:
        result = subprocess.run(
            ["node", bridge_path, "init", "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if "success" in result.stdout:
            print("  ✅ Wallet bridge functional")
            return True
        else:
            print(f"  ⚠️  Wallet bridge output unexpected: {result.stdout[:100]}")
            return False

    except Exception as e:
        print(f"  ❌ Error testing wallet bridge: {e}")
        return False


def check_contracts():
    """Check if smart contracts exist"""
    print("\nChecking smart contracts...")

    contract_path = "contracts/HyphaEscrow.sol"
    if not os.path.exists(contract_path):
        print(f"  ❌ {contract_path} not found")
        return False

    print("  ✅ HyphaEscrow.sol exists")

    deploy_script = "scripts/deploy.js"
    if not os.path.exists(deploy_script):
        print(f"  ❌ {deploy_script} not found")
        return False

    print("  ✅ Deployment script exists")
    return True


def main():
    print("=" * 60)
    print("HYPHA Beta Launch - Setup Verification")
    print("=" * 60)

    results = {
        "Environment file": check_env_file(),
        "Python packages": check_python_packages(),
        "Node.js packages": check_nodejs_packages(),
        "WDK wallet bridge": check_wallet_bridge(),
        "Smart contracts": check_contracts()
    }

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, passed in results.items():
        status = "✅ READY" if passed else "❌ NOT READY"
        print(f"{name:25} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)

    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("\nYou're ready for Phase 2: Smart Contract Deployment!")
        print("\nNext step:")
        print("  npm run deploy:testnet")
        print("\nMake sure you have Base Sepolia ETH in your wallet first.")
        print("Faucet: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nAction required:")

        if not results["Environment file"]:
            print("  1. Add your testnet private key to .env")
            print("     nano .env")
            print("     Replace: PRIVATE_KEY=your_private_key_here")
            print("     With:    PRIVATE_KEY=0x...")

        if not results["Python packages"]:
            print("  2. Install Python packages:")
            print("     python3 -m pip install web3 pynacl pytest")

        if not results["Node.js packages"]:
            print("  3. Install Node.js packages:")
            print("     npm install")

        print("\nSee BETA_SETUP_STATUS.md for detailed instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
