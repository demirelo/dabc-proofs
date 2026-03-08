// SPDX-License-Identifier: LGPL-3.0-only
pragma solidity 0.8.28;

import {PackedSegment} from "@iss/types/PackedSegment_v1.sol";
import {PackedSegmentLib} from "@iss/libraries/PackedSegmentLib.sol";

/// @title  Certora harness for PackedSegmentLib
/// @notice Exposes library functions as external calls for CVL verification.
contract PackedSegmentHarness {
    using PackedSegmentLib for PackedSegment;

    function create(
        uint initialPrice,
        uint priceIncrease,
        uint supplyPerStep,
        uint numberOfSteps
    ) external pure returns (bytes32) {
        PackedSegment seg = PackedSegmentLib._create(
            initialPrice, priceIncrease, supplyPerStep, numberOfSteps
        );
        return PackedSegment.unwrap(seg);
    }

    function unpack(bytes32 packed)
        external
        pure
        returns (uint ip, uint pi, uint sps, uint ns)
    {
        PackedSegment seg = PackedSegment.wrap(packed);
        return seg._unpack();
    }

    function initialPrice(bytes32 packed) external pure returns (uint) {
        return PackedSegment.wrap(packed)._initialPrice();
    }

    function priceIncrease(bytes32 packed) external pure returns (uint) {
        return PackedSegment.wrap(packed)._priceIncrease();
    }

    function supplyPerStep(bytes32 packed) external pure returns (uint) {
        return PackedSegment.wrap(packed)._supplyPerStep();
    }

    function numberOfSteps(bytes32 packed) external pure returns (uint) {
        return PackedSegment.wrap(packed)._numberOfSteps();
    }
}
