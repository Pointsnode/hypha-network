# How to Get Your Private Key - Step by Step Guide

## ⚠️ CRITICAL SAFETY RULES

**BEFORE WE START**:
- ✅ We're creating a **TESTNET wallet only** (for fake money on Base Sepolia)
- ✅ This wallet is **ONLY for testing** - never use it on mainnet
- ✅ Never share your private key with anyone (except putting it in .env)
- ❌ **NEVER** use a wallet with real money for this
- ❌ **NEVER** put mainnet private keys in .env

---

## Option 1: MetaMask (Easiest - Recommended)

### Step 1: Install MetaMask

1. Go to: https://metamask.io/download/
2. Click "Install MetaMask for Chrome" (or your browser)
3. Click "Add to Chrome"
4. Click "Create a new wallet"
5. Create a password (this is just for MetaMask app, not your private key)
6. **IMPORTANT**: Save your Secret Recovery Phrase somewhere safe
   - Write it down on paper
   - Store it securely
   - You'll need this if you ever lose access

### Step 2: Add Base Sepolia Network

1. Open MetaMask extension
2. Click the network dropdown (top left, probably says "Ethereum Mainnet")
3. Click "Add network" or "Add a network manually"
4. Enter these details:

   ```
   Network Name: Base Sepolia
   RPC URL: https://sepolia.base.org
   Chain ID: 84532
   Currency Symbol: ETH
   Block Explorer: https://sepolia.basescan.org
   ```

5. Click "Save"
6. Switch to "Base Sepolia" network

### Step 3: Get Your Private Key

1. Click the three dots (⋮) in top right of MetaMask
2. Click "Account details"
3. Click "Show private key"
4. Enter your MetaMask password
5. Click "Confirm"
6. **Copy the private key** (should start with 0x and be 66 characters)

   Example format: `0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef`

7. **Keep this window open** - you'll need it in the next step

### Step 4: Copy Your Wallet Address

1. In MetaMask, click on your account name at the top
2. Click the copy icon next to your address
3. Save this somewhere - you'll need it for the faucet

   Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1`

---

## Option 2: Using Cast/Foundry (Command Line)

If you prefer command line tools:

### Step 1: Install Foundry (if not already installed)

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Step 2: Create New Wallet

```bash
cast wallet new
```

**Output will look like**:
```
Successfully created new keypair.
Address:     0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
Private key: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**Copy both**:
- Address (for getting testnet funds)
- Private key (for .env file)

---

## Option 3: Using Python (For Developers)

If you want to generate it programmatically:

```bash
cd /Users/agent_21/Downloads/Hypha/hypha-project

python3 << 'EOF'
from eth_account import Account
import secrets

# Generate new account
private_key = "0x" + secrets.token_hex(32)
account = Account.from_key(private_key)

print("=" * 60)
print("NEW TESTNET WALLET CREATED")
print("=" * 60)
print(f"Address:     {account.address}")
print(f"Private Key: {private_key}")
print()
print("⚠️  SAVE BOTH OF THESE!")
print("=" * 60)
EOF
```

---

## ✏️ Adding Private Key to .env File

### Method 1: Using nano (Recommended)

```bash
cd /Users/agent_21/Downloads/Hypha/hypha-project
nano .env
```

**What you'll see**:
```env
# HYPHA Environment Configuration

# Blockchain (Base Sepolia Testnet)
WEB3_PROVIDER_URI=https://sepolia.base.org
PRIVATE_KEY=your_private_key_here
ESCROW_CONTRACT_ADDRESS=  # Leave empty until deployed
```

**Using nano**:
1. Use arrow keys to navigate to the `PRIVATE_KEY` line
2. Delete `your_private_key_here`
3. Paste your private key (including the 0x prefix)
4. Press `Ctrl + X` to exit
5. Press `Y` to confirm save
6. Press `Enter` to confirm filename

**After editing, the line should look like**:
```env
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

### Method 2: Using sed (One-liner)

```bash
cd /Users/agent_21/Downloads/Hypha/hypha-project

# Replace YOUR_PRIVATE_KEY with your actual key (keep the 0x)
sed -i '' 's/PRIVATE_KEY=your_private_key_here/PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE/' .env
```

### Method 3: Using VS Code or any text editor

1. Open `/Users/agent_21/Downloads/Hypha/hypha-project/.env` in your editor
2. Find line 5: `PRIVATE_KEY=your_private_key_here`
3. Replace `your_private_key_here` with your private key
4. Save the file

---

## ✅ Verification

After adding your private key, verify it's correct:

```bash
cd /Users/agent_21/Downloads/Hypha/hypha-project

# Check the .env file (will show *** for security)
grep PRIVATE_KEY .env | sed 's/\(PRIVATE_KEY=0x\).*/\1***/'
```

Should show:
```
PRIVATE_KEY=0x***
```

**Run setup verification**:
```bash
python3 verify_setup.py
```

Should show:
```
Environment file          ✅ READY
```

---

## 📝 Example: Complete Flow

**Here's the complete flow from start to finish**:

```bash
# 1. Generate wallet using Python
cd /Users/agent_21/Downloads/Hypha/hypha-project
python3 << 'EOF'
from eth_account import Account
import secrets
pk = "0x" + secrets.token_hex(32)
acc = Account.from_key(pk)
print(f"Address: {acc.address}")
print(f"Private Key: {pk}")
print(f"\nAdd this to .env:")
print(f"PRIVATE_KEY={pk}")
EOF

# 2. Copy the output private key

# 3. Edit .env
nano .env
# Paste the private key on the PRIVATE_KEY line
# Ctrl+X, Y, Enter to save

# 4. Verify
python3 verify_setup.py

# 5. Get testnet funds for the address shown
# Go to: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
# Enter your address
```

---

## 🎯 What Your .env Should Look Like After

```env
# HYPHA Environment Configuration

# Blockchain (Base Sepolia Testnet)
WEB3_PROVIDER_URI=https://sepolia.base.org
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
ESCROW_CONTRACT_ADDRESS=  # Leave empty until deployed

# USDT Contract (Base Sepolia test token)
USDT_CONTRACT_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

# P2P Network
HYPHA_SEED=your_seed_phrase_here
DHT_BOOTSTRAP_NODES=bootstrap1.hypha.network:49737

# Development
DEBUG=true
LOG_LEVEL=INFO
```

**Key points**:
- ✅ `PRIVATE_KEY` has your actual private key (66 characters starting with 0x)
- ✅ All other values stay the same
- ✅ File is saved

---

## 🆘 Troubleshooting

### "Invalid private key format"

**Problem**: Private key is wrong length or format

**Solution**:
- Must be exactly 66 characters total
- Must start with `0x`
- Followed by exactly 64 hexadecimal characters (0-9, a-f)

### "Permission denied when editing .env"

**Solution**:
```bash
chmod 644 .env
nano .env
```

### "Can't find .env file"

**Solution**:
```bash
cd /Users/agent_21/Downloads/Hypha/hypha-project
ls -la .env  # Should show the file
```

---

## 🚀 After Adding Private Key

Once your private key is in `.env`:

1. **Get testnet funds**:
   - Go to: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
   - Enter your wallet address
   - Wait for transaction to confirm

2. **Verify everything**:
   ```bash
   python3 verify_setup.py
   ```

3. **Deploy**:
   ```bash
   ./quick_deploy.sh
   ```

---

**Need help?** Let me know which option you want to use and I'll guide you through it!
