# HYPHA Development Guidelines

## Tone of Voice: Minimalist Infrastructure

All code comments, documentation, and commit messages must adhere to the Kanso (Simplicity) principle.

### Rules

1. **Remove words that don't add technical value**
2. **No marketing language in technical documentation**
3. **No emojis in code or technical docs**
4. **Focus on mechanism, not metaphor**

### Examples

**Avoid:**
```python
# 🚀 This amazing function creates a super cool wallet! 💰
def create_wallet():
    pass
```

**Prefer:**
```python
# Deterministically generates secp256k1 wallet from seed
def create_wallet():
    pass
```

**Avoid:**
```
We're excited to announce our revolutionary new feature that will transform the way agents interact!
```

**Prefer:**
```
Agents now stream context over encrypted P2P channels.
```

## Code Style

### Python
- Use type hints
- Prefer async/await over callbacks
- Document protocol-level behavior, not implementation details
- Functions: verb_noun pattern (`stream_context`, `verify_fuel`)

### JavaScript
- ES6+ syntax
- Async/await for WDK operations
- Minimal wrapper pattern over Tether WDK

### Solidity
- Explicit over implicit
- ReentrancyGuard on state-changing functions
- Events for all value transfers

## Commit Messages

Format: `<type>: <description>`

Types: `feat`, `fix`, `refactor`, `test`, `docs`

**Avoid:**
```
feat: 🎉 Added amazing new wallet feature!!!
```

**Prefer:**
```
feat: unified seed architecture for P2P + wallet
```

## Documentation Structure

1. **Problem** - Technical friction being solved
2. **Solution** - Mechanism, not benefits
3. **Code** - Minimal working example
4. **Architecture** - How components interact
5. **Integration** - How external systems use it

## Target Audience

Technical leads at:
- Tether (WDK integration partners)
- QVAC (infrastructure evaluation)
- Holepunch (P2P application developers)

Assume reader has:
- Distributed systems knowledge
- Blockchain fundamentals
- Python/JavaScript proficiency

Do not explain:
- What a seed phrase is
- How DHT works
- What async/await does

## AGI Neural Bus Strategy

HYPHA is infrastructure, not application. Position as:
- Substrate for agent coordination
- Settlement layer for autonomous economies
- Protocol, not platform

Avoid positioning as:
- AI agent marketplace
- Task automation tool
- Consumer product

## File-Specific Guidelines

### README.md
- Lead with infrastructure positioning
- Show code immediately
- Infrastructure stack table
- No emojis, no exclamation marks

### API Documentation
- Contract-first: show interface before explanation
- Failure modes: document error conditions
- Examples: working code, not pseudocode

### Comments
- Protocol decisions: why, not what
- Edge cases: document assumptions
- Complexity: explain non-obvious optimizations

## Review Checklist

Before committing documentation:
- [ ] No emojis
- [ ] No marketing language ("revolutionary", "amazing", "game-changing")
- [ ] No unnecessary adjectives
- [ ] Code examples are minimal and executable
- [ ] Technical terms are precise
- [ ] Target audience is technical leads, not general public
