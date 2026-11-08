#!/usr/bin/env python3
"""Inspect mt76 Connac2 firmware trailer and feature TLVs without guessing extensions."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

TRAILER_SIZE = 36
REGION_SIZE = 40
FEATURE_TAG = 4
FEATURE_COMMON_SIZE = 16

class FirmwareFormatError(ValueError):
    pass

def u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise FirmwareFormatError("truncated 16-bit field")
    return struct.unpack_from("<H", data, offset)[0]

def parse_firmware(data: bytes) -> dict[str, object]:
    if len(data) < TRAILER_SIZE:
        raise FirmwareFormatError("firmware is shorter than its trailer")
    trailer_offset = len(data) - TRAILER_SIZE
    chip_id, eco, region_count = data[trailer_offset:trailer_offset + 3]
    if region_count == 0:
        raise FirmwareFormatError("firmware declares zero regions")
    region_offset = trailer_offset - region_count * REGION_SIZE
    if region_offset < 0:
        raise FirmwareFormatError("region descriptor table exceeds firmware bounds")
    region_lengths = []
    for index in range(region_count):
        descriptor = region_offset + index * REGION_SIZE
        region_length = struct.unpack_from("<I", data, descriptor + 20)[0]
        region_lengths.append(region_length)
    region_data_length = sum(region_lengths)
    metadata_offset = region_data_length + 16
    if metadata_offset < 16 or metadata_offset + 4 > region_offset:
        raise FirmwareFormatError("release metadata offset is outside the metadata area")
    outer_length, outer_pad, outer_tag = struct.unpack_from("<HBB", data, metadata_offset)
    outer_start = metadata_offset + 4
    outer_end = outer_start + outer_length
    outer_padded_end = outer_end + outer_pad
    if outer_end < outer_start or outer_padded_end > region_offset:
        raise FirmwareFormatError("outer release-info length or padding exceeds metadata boundary")
    tlvs = []
    cursor = outer_start
    while cursor < outer_end:
        if cursor + 4 > outer_end:
            raise FirmwareFormatError("truncated TLV header")
        length, pad, tag = struct.unpack_from("<HBB", data, cursor)
        payload_start = cursor + 4
        payload_end = payload_start + length
        next_cursor = payload_end + pad
        if payload_end < payload_start or next_cursor > outer_end:
            raise FirmwareFormatError("TLV payload or padding exceeds outer boundary")
        payload = data[payload_start:payload_end]
        item: dict[str, object] = {"tag": tag, "length": length, "pad": pad}
        if tag == FEATURE_TAG:
            if length < FEATURE_COMMON_SIZE:
                raise FirmwareFormatError("feature TLV is shorter than common 16-byte structure")
            item["segment"] = payload[0]
            item["data"] = payload[1]
            item["cnm_bit_7"] = bool(payload[1] & 0x80)
            item["common_reserved_hex"] = payload[2:16].hex()
            item["extension_hex"] = payload[16:].hex()
        tlvs.append(item)
        cursor = next_cursor
    if cursor != outer_end:
        raise FirmwareFormatError("TLV sequence does not end at outer boundary")
    feature_tlvs = [item for item in tlvs if item["tag"] == FEATURE_TAG]
    if len(feature_tlvs) != 1:
        raise FirmwareFormatError("expected exactly one feature TLV")
    fw_version = data[trailer_offset + 7:trailer_offset + 17].decode("ascii", "replace").rstrip("\x00")
    build_date = data[trailer_offset + 17:trailer_offset + 32].decode("ascii", "replace").rstrip("\x00")
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "chip_id": chip_id,
        "eco_code": eco,
        "region_count": region_count,
        "region_lengths": region_lengths,
        "region_descriptor_offset": region_offset,
        "metadata_offset": metadata_offset,
        "outer_release_info": {"length": outer_length, "pad": outer_pad, "tag": outer_tag},
        "firmware_version": fw_version,
        "build_date": build_date,
        "tlvs": tlvs,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("firmware", type=Path)
    args = parser.parse_args()
    try:
        report = parse_firmware(args.firmware.read_bytes())
    except (OSError, FirmwareFormatError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()