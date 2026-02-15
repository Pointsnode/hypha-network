# 🚀 START HERE - HYPHA Quick Navigation

Welcome to HYPHA! This guide will get you up and running in 15 minutes.

## 📖 Quick Navigation

### For First-Time Setup
1. **[DEPLOY_COMMANDS.md](DEPLOY_COMMANDS.md)** ⭐ START HERE
   - Copy-paste commands to deploy
   - Fastest path to working system
   - ~15 minutes total

2. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**
   - Detailed step-by-step instructions
   - Troubleshooting included
   - Read if you want to understand each step

3. **[GETTING_STARTED.md](GETTING_STARTED.md)**
   - SDK usage guide
   - API reference
   - Architecture overview

### For Understanding the Project
- **[README.md](README.md)** - Project overview
- **[BUILD_SUMMARY.md](BUILD_SUMMARY.md)** - What we built
- **[BLITZ_ROADMAP.md](BLITZ_ROADMAP.md)** - 6-month plan

### For Next Steps
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Development roadmap
- **[examples/](examples/)** - Working code examples

### When Things Go Wrong
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues & fixes

---

## ⚡ Ultra-Quick Start (30 seconds)

```bash
# 1. Install
npm install && pip install -r requirements.txt

# 2. Test setup
./quick_test.sh

# 3. Follow instructions from test output
```

---

## 🎯 Your 15-Minute Path

### Minutes 0-5: Installation
```bash
cd hypha-project
npm install
pip install -r requirements.txt
```

### Minutes 5-7: Configuration
```bash
cp .env.example .env
nano .env  # Add your PRIVATE_KEY
```

### Minutes 7-10: Get Testnet ETH
Visit: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet

### Minutes 10-12: Deploy
```bash
npm run compile
npm run deploy:testnet
# Add contract address to .env
```

### Minutes 12-15: Test
```bash
# Terminal 1
python3 hypha_connect.py --mode provider

# Terminal 2
python3 hypha_connect.py --mode buyer
```

---

## 📚 Documentation Map

```
hypha-project/
│
├── START_HERE.md          ← You are here
│
├── 🚀 DEPLOYMENT
│   ├── DEPLOY_COMMANDS.md     Copy-paste commands
│   ├── DEPLOYMENT_GUIDE.md    Detailed instructions
│   └── quick_test.sh          Test your setup
│
├── 📖 GUIDES
│   ├── GETTING_STARTED.md     SDK usage & API
│   ├── BUILD_SUMMARY.md       Technical details
│   └── TROUBLESHOOTING.md     Problem solving
│
├── 🎯 PLANNING
│   ├── BLITZ_ROADMAP.md       Strategic roadmap
│   └── NEXT_STEPS.md          Development tasks
│
└── 💻 CODE
    ├── hypha_sdk/             Python SDK
    ├── contracts/             Smart contracts
    ├── src/discovery/         P2P networking
    ├── examples/              Working demos
    └── scripts/               Deployment tools
```

---

## ✅ Success Criteria

You'll know everything works when:

- [ ] `./quick_test.sh` shows all tests passing
- [ ] `npm run deploy:testnet` deploys successfully
- [ ] P2P discovery finds peers
- [ ] SDK can create agents
- [ ] Escrow contract responds

---

## 🆘 Quick Help

### "Where do I start?"
→ [DEPLOY_COMMANDS.md](DEPLOY_COMMANDS.md)

### "Something's broken"
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### "How do I use the SDK?"
→ [GETTING_STARTED.md](GETTING_STARTED.md)

### "What did we build?"
→ [BUILD_SUMMARY.md](BUILD_SUMMARY.md)

### "What's next?"
→ [NEXT_STEPS.md](NEXT_STEPS.md)

---

## 🎓 Learning Path

1. **Complete beginner**
   - Read README.md
   - Follow DEPLOY_COMMANDS.md
   - Run examples/

2. **Want to understand internals**
   - Read BUILD_SUMMARY.md
   - Study contracts/HyphaEscrow.sol
   - Review hypha_sdk/core.py

3. **Ready to build**
   - Read GETTING_STARTED.md
   - Try examples/complete_workflow.py
   - Modify and experiment

4. **Want to contribute**
   - Read NEXT_STEPS.md
   - Check BLITZ_ROADMAP.md
   - Start with Week 2 tasks

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `hypha_sdk/core.py` | Main SDK - Agent class |
| `contracts/HyphaEscrow.sol` | Smart contract |
| `src/discovery/bridge.js` | P2P discovery |
| `.env` | Your configuration |
| `package.json` | Node.js scripts |

---

## 💡 Pro Tips

1. **Always start with** `./quick_test.sh`
2. **Use testnet** (free) before mainnet
3. **Keep .env secure** (never commit)
4. **Check balance** before transactions
5. **Read error messages** - they're helpful!

---

## 🚀 Ready?

```bash
# Run this now:
./quick_test.sh
```

Then follow the output instructions!

---

**Next:** [DEPLOY_COMMANDS.md](DEPLOY_COMMANDS.md) for copy-paste deployment commands.
