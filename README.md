# Debt-Aware Discrete Bonding Curves (DABC)

Paper and formal verification artifacts for *Debt-Aware Discrete Bonding Curves*.

## Paper

- **[dabc-2026.pdf](dabc-2026.pdf)** — full manuscript

## Formal Verification Artifacts

The `certora/` directory contains the Certora CVL specifications, Solidity harnesses, and configuration files used to formally verify the mechanism's core properties.

### Specifications (`certora/specs/`)

| Spec | Properties | Rules |
|------|-----------|-------|
| **FloorMonotonicity** | Floor price can only increase or stay the same | 3 |
| **ReserveSolvency** | Reserve function is monotonic in supply; mulDivUp monotonicity lemma | 5 (+1 envfree) |
| **BuySellSafety** | No overspend, no free tokens, no round-trip profit, price consistency | 8 (+1 envfree) |
| **LoanSafety** | Floor-anchored LTV bounds, debt requires tokens, more debt requires more tokens | 3 |
| **RepaymentRatio** | Repayment ratio preserved, unlock does not exceed locked, no underflow | 3 |
| **SegmentValidity** | Segment encoding round-trips, invalid configurations rejected | 5 |

**Total: 6 property groups, 24 rules — all verified.**

### Harnesses (`certora/harnesses/`)

Solidity contracts that expose internal library functions to the Certora prover:

- `DiscreteCurveMathHarness.sol` — reserve computation, segment arithmetic, mulDivUp pair
- `PackedSegmentHarness.sol` — packed segment encoding/decoding
- `RepaymentHarness.sol` — repayment ratio arithmetic

### Configuration (`certora/conf/`)

Certora run configurations for each spec, specifying harness contracts, loop iteration bounds, and SMT solver timeouts.

## License

The formal verification artifacts (specs, harnesses, configs) are provided for review and reproducibility. The underlying smart contract source code is licensed separately under BUSL-1.1.
