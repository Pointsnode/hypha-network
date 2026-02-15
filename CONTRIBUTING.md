# Contributing to HYPHA

## The Mycelial Philosophy

HYPHA is the nervous system of the AGI economy. Contributions must follow three core principles:

### 1. Stateless by Default
Avoid local databases. Use the DHT for peer state and WDK for value transfer. HYPHA is transport infrastructure, not a data warehouse.

**Rationale**: Centralized state introduces synchronization overhead and custody liability. Agents maintain local memory; HYPHA provides the interconnect.

**Example violations**:
- Adding SQLite for "caching peer information"
- Implementing server-side session storage
- Creating message queues that persist beyond connection lifetime

**Correct approach**: Ephemeral Persistence—data exists only during active P2P connection.

### 2. Atomic Velocity
Features should be single-purpose. If a PR adds more than 100 lines of code, it's likely too complex.

**Rationale**: The 100-line soft limit forces decomposition into atomic primitives. Complex features should be composed from multiple small PRs, not delivered as monolithic changesets.

**Process**:
- Features >100 LOC: Open a Discussion first, propose decomposition
- Features <100 LOC: Direct PR with impact statement
- Refactors: No line limit, but must maintain API compatibility

### 3. Tether-Native
All financial logic must leverage the Tether WDK. Do not reinvent wallet primitives.

**Rationale**: HYPHA is Tether infrastructure. Custom wallet implementations fragment the ecosystem and introduce security surface.

**Requirements**:
- Use `@tetherto/wdk` packages (official releases only)
- Wallet operations must go through `wallet_bridge.js`
- No direct secp256k1 transaction signing outside WDK

## Kanso Coding Standard

Follow the Kanso (Simplicity) principle: if code doesn't reduce friction, delete it.

### Python Requirements
- **Version**: Python 3.11+ (required for performance improvements in asyncio)
- **Type Hints**: Strict typing on all public functions
- **Async**: Prefer async/await over threading
- **Imports**: Explicit imports, no `from module import *`

### Code Style
```python
# Good: Explicit, typed, purpose-clear
async def stream_context(self, state: bytes, peer_id: bytes) -> None:
    """Stream binary state to peer over encrypted channel."""
    await self._dht.send(peer_id, state)

# Bad: Implicit, untyped, vague naming
def send_stuff(self, data, who):
    self.thing.do(who, data)
```

### Documentation Standard
- **Functions**: Docstring describes protocol behavior, not implementation
- **Classes**: State machine diagram for complex lifecycle
- **Modules**: Single-line purpose statement at top

**Example**:
```python
"""
Binary state streaming over Hyperswarm DHT.

Implements ephemeral persistence: state exists only during active connection.
"""
```

### Testing Requirements
Every new primitive must include a P2P connectivity test using two local processes.

**Minimum test structure**:
```python
async def test_handshake():
    """Two agents discover each other and exchange wallet addresses."""
    agent_a = HyphaNutrient(seed_a)
    agent_b = HyphaNutrient(seed_b)

    await asyncio.gather(agent_a.start(), agent_b.start())

    # Verify P2P connection established
    assert agent_a.get_peer_count() > 0
    assert agent_b.get_peer_count() > 0
```

## Contribution Workflow

### 1. Find an Issue
Look for labels:
- `good-first-issue`: Simple, well-defined tasks
- `nutrient-rail`: Core protocol enhancements
- `wdk-integration`: Tether WDK improvements
- `friction-reduction`: Performance optimizations

### 2. Draft a SEP (Slight Enhancement Proposal)
For major architectural changes, open a Discussion first.

**When to write a SEP**:
- New protocol primitives (e.g., multi-party escrow)
- Breaking API changes
- Dependencies on unreleased WDK features

**SEP Template**:
```
## Problem
What systemic friction does this address?

## Solution
What primitive does this introduce?

## Impact
Latency reduction or trust assumption removal.
```

### 3. The "Pulse" PR
Every Pull Request must include an **Impact** section explaining how this reduces Systemic Friction.

**PR Template**:
```markdown
## Changes
- Added binary state compression (zstd)

## Impact
Reduces state transfer time from 45ms to 12ms for 10KB context snapshots.
Decreases bandwidth consumption by 60% on metered connections.

## Tests
- test_compression_ratio()
- test_decompression_speed()
```

### 4. Review Process
- **Automated checks**: Type checking (mypy), linting (ruff), tests (pytest)
- **Human review**: Focus on protocol correctness and friction analysis
- **Merge criteria**: All tests pass + 1 maintainer approval

## Anti-Patterns

### Don't Add Abstraction Layers
HYPHA is minimalist infrastructure. Avoid "framework-ification."

**Bad**:
```python
class AgentFactory:
    def create_agent(self, config: dict) -> BaseAgent:
        # 200 lines of factory logic
```

**Good**:
```python
agent = HyphaNutrient(seed)  # Direct instantiation
```

### Don't Add Configuration Files
Configuration is code. Use environment variables or constructor parameters.

**Bad**: `config.yaml` with 50 parameters

**Good**: `.env` with 5 essential parameters

### Don't Add Middleware
Every abstraction layer adds latency. Talk directly to Hyperswarm and WDK.

**Bad**: "Connection pool manager" wrapping DHT

**Good**: Direct DHT calls with error handling

## Code Review Checklist

Before submitting:
- [ ] Type hints on all public functions
- [ ] Docstrings describe protocol behavior
- [ ] Tests verify P2P connectivity
- [ ] PR includes Impact section
- [ ] LOC delta <100 (or justified in Discussion)
- [ ] No new database dependencies
- [ ] Financial logic uses WDK exclusively

## Developer Setup

```bash
git clone https://github.com/Pointsnode/hypha-network.git
cd hypha-network
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
npm install
pytest tests/
```

## Community

- **GitHub Discussions**: Architecture proposals and SEPs
- **Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions

## License

All contributions are licensed under MIT. By contributing, you agree to license your work under the same terms.

---

**Goal**: Build the IP layer for the AGI economy. High signal. Low noise. Zero friction.
