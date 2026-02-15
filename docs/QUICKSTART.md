# HYPHA Quick Start (5 minutes)

## Installation

```bash
# Clone or create project
git clone <repo-url>  # or use setup script

# Install dependencies
pip install -r requirements.txt
npm install  # for Hyperswarm bridge
```

## Your First P2P Connection

```python
from hypha_sdk import Agent

# Create agent with identity
agent = Agent()

# Hire another agent (discovery + messaging + payment)
escrow_id = await agent.hire(
    peer="agent_abc123",
    amount=10.0,
    task="Process this data"
)

# Check balance
balance = agent.check_balance()
```

## Running Tests

```bash
# P2P connectivity test
python hypha_connect.py --mode provider

# In another terminal
python hypha_connect.py --mode buyer

# Full test suite
pytest tests/
```

## Next Steps

- Read [Architecture Overview](ARCHITECTURE.md)
- Review [API Reference](API_PYTHON.md)
- Explore [examples/](../examples/)
