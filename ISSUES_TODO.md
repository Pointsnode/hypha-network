# GitHub Issues To File

> Concrete issues to file on `Pointsnode/hypha-network` to make the repo organized and inviting to contributors.

---

## 🔴 Bugs (P0 — Must Fix)

### 1. `npm install` fails with EACCES permission error
**Labels**: `bug`, `setup`
**Description**: `npm install` fails due to npm cache permission issues (`EACCES: permission denied, mkdir '/Users/.../.npm/_cacache/...'`). This blocks all Node.js functionality (Hyperswarm P2P, WDK wallet bridge).
**Fix**: Document workaround (`npm install --cache ./.npm-cache`) or add to Makefile.

### 2. `hypha_connect.py` missing `import os`
**Labels**: `bug`
**Description**: `hypha_connect.py` uses `os.urandom()` in `_generate_seed()` but never imports `os`. Running the script as standalone fails with `NameError`.
**Fix**: Add `import os` at top of file.

### 3. `examples/three_lines.py` uses invalid peer address
**Labels**: `bug`, `examples`
**Description**: The example passes `peer="agent_xyz123"` to `agent.hire()`, but `hire()` validates Ethereum addresses. This example crashes immediately.
**Fix**: Use a valid Ethereum address or create a mock/demo mode.

### 4. `setup.py` URLs point to wrong repository
**Labels**: `bug`, `packaging`
**Description**: `setup.py` references `github.com/hypha-network/hypha-sdk` but the actual repo is `github.com/Pointsnode/hypha-network`.
**Fix**: Update all URLs in setup.py.

### 5. Python path hacks in examples
**Labels**: `bug`, `dx`
**Description**: Every example file has `sys.path.insert(0, ...)` to find parent modules. This breaks if run from a different directory and won't work for pip-installed packages.
**Fix**: Proper package structure with `pip install -e .` support.

---

## 🟡 Improvements (P1)

### 6. Add LICENSE file
**Labels**: `documentation`
**Description**: README says MIT license but no `LICENSE` file exists in the repo. This is required for proper open-source status and PyPI publishing.

### 7. Add `pyproject.toml` for modern Python packaging
**Labels**: `enhancement`, `packaging`
**Description**: Replace `setup.py` with `pyproject.toml` (PEP 621). Enables cleaner `pip install`, proper metadata, and tool configuration (ruff, mypy, pytest).

### 8. Create a working local demo that doesn't require Node.js
**Labels**: `enhancement`, `dx`, `good first issue`
**Description**: Currently all demos require Node.js + npm for Hyperswarm/WDK bridges. Create a `demo_local.py` that demonstrates:
- Agent creation and seed derivation
- Contract read operations (check balance, read escrow status)
- SDK capabilities without full P2P stack

### 9. Add GitHub Actions CI pipeline
**Labels**: `enhancement`, `ci`
**Description**: No CI currently. Add workflow for:
- Python tests on 3.9, 3.10, 3.11, 3.12
- Linting (ruff)
- Type checking (mypy)
- Contract compilation check

### 10. Add type hints throughout SDK
**Labels**: `enhancement`, `good first issue`
**Description**: Some functions have type hints, others don't. Add comprehensive type hints and a `py.typed` marker for downstream consumers.

### 11. WDK wallet bridge is a mock
**Labels**: `enhancement`, `blockchain`
**Description**: `hypha_sdk/wallet_wdk.py` header says "Currently using mock WDK bridge until Tether packages can be installed." Need to implement real WDK integration or clearly document mock status.

### 12. Add Makefile for common operations
**Labels**: `enhancement`, `dx`
**Description**: Create Makefile with targets: `install`, `test`, `lint`, `demo`, `deploy-testnet`, `clean`.

---

## 🟢 Features (P2)

### 13. LangChain integration — `HyphaTool`
**Labels**: `enhancement`, `integration`, `help wanted`
**Description**: Create a LangChain-compatible tool that allows LLM agents to hire other Hypha agents. `from hypha.integrations.langchain import HyphaTool`

### 14. CrewAI integration — `HyphaAgent`
**Labels**: `enhancement`, `integration`, `help wanted`
**Description**: Create a CrewAI-compatible agent wrapper that gives CrewAI agents self-custodial wallets and P2P discovery.

### 15. Agent reputation system
**Labels**: `enhancement`, `blockchain`
**Description**: On-chain reputation derived from completed escrow history. Agents can check peer reputation before engaging.

### 16. CLI tool — `hypha` command
**Labels**: `enhancement`, `dx`
**Description**: CLI entry point for common operations:
- `hypha init` — create `.env` and seed
- `hypha status` — check contract, balance, peers
- `hypha demo` — run interactive demo
- `hypha deploy` — deploy escrow contract

### 17. Docker support
**Labels**: `enhancement`, `dx`
**Description**: `Dockerfile` + `docker-compose.yml` for zero-config development environment. Solves npm permission issues and ensures consistent environment.

### 18. Google Colab quickstart notebook
**Labels**: `enhancement`, `documentation`, `good first issue`
**Description**: Jupyter notebook that runs in Colab, demonstrating full Hypha workflow without local setup.

### 19. Multi-party escrow support
**Labels**: `enhancement`, `blockchain`
**Description**: Extend `HyphaEscrow.sol` to support pipeline payments where Agent A pays B who pays C, with chained escrows.

### 20. Event indexer / analytics dashboard
**Labels**: `enhancement`, `frontend`
**Description**: Index `EscrowCreated`, `EscrowCompleted` events. Simple dashboard showing network activity, volume, active agents.

---

## 📝 Documentation

### 21. Architecture diagram in README
**Labels**: `documentation`
**Description**: Add ASCII or Mermaid architecture diagram showing: Seed → P2P Identity + Wallet, Hyperswarm DHT, Base L2 settlement, Escrow contract flow.

### 22. "Build Your First Agent Economy" tutorial
**Labels**: `documentation`, `good first issue`
**Description**: Step-by-step tutorial walking through a complete buyer-provider workflow with real testnet transactions.

### 23. API reference auto-generation
**Labels**: `documentation`
**Description**: Set up pdoc or sphinx to auto-generate API docs from docstrings. Host on GitHub Pages.

### 24. Improve CONTRIBUTING.md with setup instructions
**Labels**: `documentation`
**Description**: Current CONTRIBUTING.md is philosophical. Add practical setup instructions, coding standards, PR process.

---

## Filing Priority

**File immediately** (makes repo look active):
- #6 (LICENSE), #8 (local demo), #9 (CI), #12 (Makefile), #21 (arch diagram)

**File this week** (attract contributors):
- #10, #13, #14, #18 — all tagged `good first issue` or `help wanted`

**File when Phase 1 complete**:
- #15, #16, #17, #19, #20 — bigger features for the roadmap
