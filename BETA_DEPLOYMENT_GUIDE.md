# HYPHA Beta Deployment Guide

## 🎉 Current Status

Your HYPHA infrastructure is **fully deployed** and ready:

- ✅ **Smart Contract**: Deployed to Base Sepolia at `0x7bBf8A3062a8392B3611725c8D983d628bA11E6F`
- ✅ **Contract Verified**: Source code visible on Basescan
- ✅ **All Tests Passing**: 19/19 smart contract tests pass
- ✅ **WDK Integration**: Tether WDK working with real packages
- ✅ **P2P Networking**: Hyperswarm discovery tested and working

**View your contract**: https://sepolia.basescan.org/address/0x7bBf8A3062a8392B3611725c8D983d628bA11E6F#code

---

## 🚀 What's Next: Deploy Beta Agents

You have **two deployment options**:

### Option 1: Deploy Locally (Recommended for Testing)
Run agents on your machine to test the beta

### Option 2: Deploy to Production
Deploy agents to cloud servers for 24/7 operation

---

## 📦 Option 1: Deploy Locally (Start Here)

### Step 1: Create a Provider Agent

This agent will accept tasks and earn USDT:

**File**: `examples/provider_agent.py`

```python
#!/usr/bin/env python3
"""
HYPHA Provider Agent - Accepts tasks and earns USDT
"""

import asyncio
import hashlib
from hypha_nutrient import HyphaNutrient

async def run_provider():
    """Run a provider agent that accepts tasks"""

    # Create deterministic seed for this agent
    seed = hashlib.sha256(b"provider-agent-alpha").digest()

    # Initialize agent
    agent = HyphaNutrient(seed=seed)

    print("=" * 60)
    print("🤖 HYPHA Provider Agent Started")
    print("=" * 60)
    print(f"Node ID: {agent.node_id.hex()[:16]}...")
    print(f"Wallet:  {agent.get_wallet_address()}")
    print(f"Network: Base Sepolia")
    print("=" * 60)

    # Start P2P discovery
    await agent.start()

    print("\n✅ Provider ready - listening for tasks...")
    print("   Press Ctrl+C to stop\n")

    # Keep running and accepting tasks
    try:
        while True:
            # Check for fuel
            has_fuel = agent.verify_fuel(min_usdt=0.1)

            # Stream status every 30 seconds
            await asyncio.sleep(30)
            await agent.stream_context({
                "type": "provider",
                "status": "ready",
                "has_fuel": has_fuel,
                "wallet": agent.get_wallet_address()
            })

    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down provider...")
        await agent.stop()
        print("✅ Provider stopped")

if __name__ == "__main__":
    asyncio.run(run_provider())
```

### Step 2: Create a Buyer Agent

This agent creates tasks and pays providers:

**File**: `examples/buyer_agent.py`

```python
#!/usr/bin/env python3
"""
HYPHA Buyer Agent - Creates tasks and pays providers
"""

import asyncio
import hashlib
from hypha_sdk.core import Agent

async def run_buyer():
    """Run a buyer agent that creates tasks"""

    # Initialize buyer agent
    buyer = Agent()

    print("=" * 60)
    print("💰 HYPHA Buyer Agent Started")
    print("=" * 60)
    print(f"Wallet: {buyer.account.address}")
    print(f"Network: Base Sepolia")
    print("=" * 60)

    # Example: Create an escrow for a task
    provider_address = "0x..." # Replace with provider wallet address

    print(f"\n📝 Creating task escrow...")
    print(f"   Provider: {provider_address}")
    print(f"   Amount: 1.0 USDT")
    print(f"   Task: Beta test task - Image processing")

    try:
        escrow_id = await buyer.hire(
            peer=provider_address,
            amount=1.0,  # 1 USDT
            task="Beta test task: Process and analyze images"
        )

        print(f"\n✅ Task created!")
        print(f"   Escrow ID: {escrow_id.hex()}")
        print(f"   View on Basescan: https://sepolia.basescan.org/tx/{escrow_id.hex()}")

    except Exception as e:
        print(f"\n❌ Error creating task: {e}")
        return

    print("\n✅ Buyer agent complete")

if __name__ == "__main__":
    asyncio.run(run_buyer())
```

### Step 3: Run the Agents

**Terminal 1 - Provider**:
```bash
cd /Users/agent_21/Downloads/Hypha/hypha-project
python3 examples/provider_agent.py
```

**Terminal 2 - Buyer**:
```bash
cd /Users/agent_21/Downloads/Hypha/hypha-project
python3 examples/buyer_agent.py
```

---

## 🌐 Option 2: Deploy to Production

### Deploy to Cloud Server

**1. Choose a Platform**:
- **DigitalOcean**: $6/month droplet
- **AWS EC2**: t3.micro instance
- **Heroku**: Free/hobby tier
- **Railway**: Simple deployment

**2. Setup Script** (`deploy_server.sh`):

```bash
#!/bin/bash
# Deploy HYPHA agent to Ubuntu server

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3 python3-pip python3-venv -y

# Install Node.js (for WDK)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Clone your repo (or upload files)
cd /home/ubuntu
git clone YOUR_REPO_URL hypha
cd hypha

# Install dependencies
npm install
pip3 install -r requirements.txt

# Create .env
cat > .env << EOF
WEB3_PROVIDER_URI=https://sepolia.base.org
PRIVATE_KEY=YOUR_PRIVATE_KEY
ESCROW_CONTRACT_ADDRESS=0x7bBf8A3062a8392B3611725c8D983d628bA11E6F
USDT_CONTRACT_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e
EOF

# Run with systemd
sudo tee /etc/systemd/system/hypha-provider.service > /dev/null << EOF
[Unit]
Description=HYPHA Provider Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/hypha
ExecStart=/usr/bin/python3 examples/provider_agent.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable hypha-provider
sudo systemctl start hypha-provider

# Check status
sudo systemctl status hypha-provider
```

**3. Monitor Your Agent**:
```bash
# View logs
sudo journalctl -u hypha-provider -f

# Check status
sudo systemctl status hypha-provider

# Restart
sudo systemctl restart hypha-provider
```

---

## 📊 Monitor Your Deployment

### Dashboard Script

**File**: `monitor_beta.py`

```python
#!/usr/bin/env python3
"""Monitor HYPHA beta deployment"""

import asyncio
from hypha_sdk.core import Agent
from hypha_sdk.health import HealthCheck

async def monitor():
    """Monitor beta deployment"""
    agent = Agent()
    health = HealthCheck(agent)

    print("=" * 60)
    print("HYPHA Beta Monitoring Dashboard")
    print("=" * 60)

    while True:
        status = await health.check_all()

        print(f"\n[{status['timestamp']}]")
        print(f"  Web3:     {status['web3']['status']}")
        print(f"  Block:    {status['web3']['block']}")
        print(f"  Balance:  {status['account']['balance']} ETH")
        print(f"  Contract: {status['contracts']['status']}")

        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor())
```

Run it:
```bash
python3 monitor_beta.py
```

---

## ✅ Quick Start Checklist

### For Local Testing:

- [ ] Create `examples/provider_agent.py` (copy from above)
- [ ] Create `examples/buyer_agent.py` (copy from above)
- [ ] Run provider in Terminal 1
- [ ] Run buyer in Terminal 2
- [ ] Watch transactions on Basescan

### For Production:

- [ ] Choose cloud platform
- [ ] Create server instance
- [ ] Upload deployment script
- [ ] Run deployment
- [ ] Monitor with systemd
- [ ] Check logs

---

## 🎯 Success Metrics

Track these during beta:

- **Agents Deployed**: Target 3-5
- **Transactions**: Target 10+
- **P2P Discovery Rate**: Target >95%
- **Transaction Success**: Target 100%
- **Uptime**: Target 99%+

---

## 🆘 Troubleshooting

### Agent Won't Start
```bash
# Check Python version
python3 --version  # Need 3.10+

# Check dependencies
pip3 list | grep web3
npm list @tetherto/wdk
```

### P2P Discovery Failing
- Check firewall allows outbound connections
- Verify DHT bootstrap nodes accessible
- Try different network environment

### Transaction Failing
- Check wallet has testnet ETH for gas
- Verify contract address in .env
- Check Basescan for error message

---

## 📞 Next Steps

1. **Start with local deployment** - Test agents on your machine
2. **Monitor transactions** - Watch on Basescan
3. **Deploy to cloud** - Scale up when ready
4. **Invite beta testers** - Share deployment guide
5. **Collect feedback** - Iterate based on usage

---

## 🔗 Important Links

- **Your Contract**: https://sepolia.basescan.org/address/0x7bBf8A3062a8392B3611725c8D983d628bA11E6F
- **Your Wallet**: https://sepolia.basescan.org/address/0x6794F4A70719f242413098024E3bAf7CA01B56EB
- **Base Faucet**: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet

---

**Ready to deploy your first agents!** 🚀
