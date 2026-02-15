---
name: Bug Report
about: Report a protocol or integration issue
title: '[BUG] '
labels: bug
assignees: ''
---

## Observed Behavior

**What is happening?**

Describe the current behavior in technical terms.

## Expected Behavior

**What should happen according to the protocol specification?**

Reference documentation or code comments if applicable.

## Reproduction Steps

**Minimal code to reproduce:**

```python
# Provide executable code that demonstrates the issue
from hypha_nutrient import HyphaNutrient

async def reproduce():
    agent = HyphaNutrient(seed)
    await agent.start()
    # Issue occurs here...
```

**Environment:**
- Python version:
- Node.js version:
- Operating system:
- Network: (Base Sepolia / Local / Mainnet)

## Impact Analysis

**How does this affect AGI coordination or settlement?**

- [ ] P2P discovery fails
- [ ] State streaming corrupted
- [ ] Wallet operations fail
- [ ] Escrow settlement blocked
- [ ] Performance degradation: Quantify (e.g., +50ms latency)

## Diagnostic Information

**Relevant logs:**
```
Paste error messages or stack traces
```

**Network conditions:**
- Peer count:
- DHT connectivity:
- Blockchain RPC status:

## Proposed Fix

**What component needs modification?**

If you've identified the root cause, describe the fix location:
- File:
- Function:
- Line:

## Workaround

**Is there a temporary workaround?**

Describe any manual steps that bypass the issue.
