// =============================================================================
// Property 5: Segment Validity
// =============================================================================
// Proves that PackedSegmentLib._create enforces floor segment constraints:
//   - A valid floor segment has exactly 1 step and 0 priceIncrease
//   - Multi-step flat segments are rejected
//   - Single-step segments with priceIncrease > 0 are rejected
//   - Free segments (price=0, increase=0) are rejected
//   - Round-trip: pack then unpack recovers original values
// =============================================================================

using PackedSegmentHarness as harness;

methods {
    function harness.create(uint, uint, uint, uint) external returns (bytes32) envfree;
    function harness.unpack(bytes32) external returns (uint, uint, uint, uint) envfree;
    function harness.initialPrice(bytes32) external returns (uint) envfree;
    function harness.priceIncrease(bytes32) external returns (uint) envfree;
    function harness.supplyPerStep(bytes32) external returns (uint) envfree;
    function harness.numberOfSteps(bytes32) external returns (uint) envfree;
}

// ---------------------------------------------------------------------------
// Rule 5a: Floor segment round-trip encoding.
//          create(ip, 0, sps, 1) then unpack recovers (ip, 0, sps, 1).
// ---------------------------------------------------------------------------
rule floorSegmentRoundTrip(uint initialPrice, uint supplyPerStep) {
    // Valid floor segment preconditions
    require initialPrice > 0;
    require supplyPerStep > 0;

    // Bit-width bounds (72-bit price, 96-bit supply)
    require initialPrice < 2^72;
    require supplyPerStep < 2^96;

    bytes32 packed = harness.create(initialPrice, 0, supplyPerStep, 1);

    uint ip; uint pi; uint sps; uint ns;
    ip, pi, sps, ns = harness.unpack(packed);

    assert ip == initialPrice, "initialPrice mismatch";
    assert pi == 0, "priceIncrease should be 0";
    assert sps == supplyPerStep, "supplyPerStep mismatch";
    assert ns == 1, "numberOfSteps should be 1";
}

// ---------------------------------------------------------------------------
// Rule 5b: Multi-step flat segments are always rejected.
// ---------------------------------------------------------------------------
rule multiStepFlatRejected(uint initialPrice, uint supplyPerStep, uint numberOfSteps) {
    require initialPrice > 0;
    require supplyPerStep > 0;
    require numberOfSteps > 1;
    require initialPrice < 2^72;
    require supplyPerStep < 2^96;
    require numberOfSteps < 2^16;

    harness.create@withrevert(initialPrice, 0, supplyPerStep, numberOfSteps);

    assert lastReverted, "multi-step flat segment must revert";
}

// ---------------------------------------------------------------------------
// Rule 5c: Single-step with positive priceIncrease is rejected.
// ---------------------------------------------------------------------------
rule singleStepWithIncreaseRejected(uint initialPrice, uint priceIncrease, uint supplyPerStep) {
    require initialPrice > 0;
    require priceIncrease > 0;
    require supplyPerStep > 0;
    require initialPrice < 2^72;
    require priceIncrease < 2^72;
    require supplyPerStep < 2^96;

    harness.create@withrevert(initialPrice, priceIncrease, supplyPerStep, 1);

    assert lastReverted, "single-step with price increase must revert";
}

// ---------------------------------------------------------------------------
// Rule 5d: Free segments (price=0, increase=0) are always rejected.
// ---------------------------------------------------------------------------
rule freeSegmentRejected(uint supplyPerStep, uint numberOfSteps) {
    require supplyPerStep > 0;
    require numberOfSteps > 0;
    require supplyPerStep < 2^96;
    require numberOfSteps < 2^16;

    harness.create@withrevert(0, 0, supplyPerStep, numberOfSteps);

    assert lastReverted, "free segment must revert";
}

// ---------------------------------------------------------------------------
// Rule 5e: Valid multi-step sloped segment round-trips correctly.
// ---------------------------------------------------------------------------
rule slopedSegmentRoundTrip(
    uint initialPrice, uint priceIncrease,
    uint supplyPerStep, uint numberOfSteps
) {
    require initialPrice > 0;
    require priceIncrease > 0;
    require supplyPerStep > 0;
    require numberOfSteps > 1;
    require initialPrice < 2^72;
    require priceIncrease < 2^72;
    require supplyPerStep < 2^96;
    require numberOfSteps < 2^16;

    bytes32 packed = harness.create(initialPrice, priceIncrease, supplyPerStep, numberOfSteps);

    uint ip; uint pi; uint sps; uint ns;
    ip, pi, sps, ns = harness.unpack(packed);

    assert ip == initialPrice, "initialPrice mismatch";
    assert pi == priceIncrease, "priceIncrease mismatch";
    assert sps == supplyPerStep, "supplyPerStep mismatch";
    assert ns == numberOfSteps, "numberOfSteps mismatch";
}
