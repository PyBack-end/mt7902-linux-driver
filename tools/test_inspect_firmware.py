import struct
import unittest

from inspect_firmware import FirmwareFormatError, TRAILER_SIZE, parse_firmware


def fixture(
    feature_payload: bytes | None,
    *,
    outer_length_delta: int = 0,
    outer_pad: int = 0,
    include_outer_padding: bool = True,
    tlv_length_delta: int = 0,
    tlv_pad: int = 0,
    include_tlv_padding: bool = True,
    extra_tlvs: tuple[bytes, ...] = (),
) -> bytes:
    region_data_length = 64
    tlvs = []
    if feature_payload is not None:
        feature_tlv = struct.pack(
            "<HBB", len(feature_payload) + tlv_length_delta, tlv_pad, 4
        ) + feature_payload
        if include_tlv_padding:
            feature_tlv += bytes(tlv_pad)
        tlvs.append(feature_tlv)
    tlvs.extend(extra_tlvs)
    outer_payload = b"".join(tlvs)
    outer = struct.pack("<HBB", len(outer_payload) + outer_length_delta, outer_pad, 0) + outer_payload
    if include_outer_padding:
        outer += bytes(outer_pad)
    descriptor = bytearray(40)
    struct.pack_into("<I", descriptor, 20, region_data_length)
    trailer = struct.pack(
        "<BBBBB2s10s15sI",
        0x13, 0, 1, 0, 0, b"\0\0", b"TEST000001", b"20261108120000\0", 0
    )
    return bytes(region_data_length) + bytes(16) + outer + bytes(descriptor) + trailer


class FirmwareParserTests(unittest.TestCase):
    def test_parses_36_byte_mt7902_feature_payload_without_interpreting_extension(self):
        payload = bytes([0x80, 0x00]) + bytes(14) + bytes.fromhex("ff" * 16 + "ffecffff")
        report = parse_firmware(fixture(payload))
        feature = report["tlvs"][0]
        self.assertEqual(feature["length"], 36)
        self.assertEqual(feature["segment"], 0x80)
        self.assertEqual(feature["data"], 0x00)
        self.assertFalse(feature["cnm_bit_7"])
        self.assertEqual(len(feature["extension_hex"]), 40)

    def test_parses_common_16_byte_feature_payload(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        feature = parse_firmware(fixture(payload))["tlvs"][0]
        self.assertTrue(feature["cnm_bit_7"])
        self.assertEqual(feature["extension_hex"], "")

    def test_accepts_bounded_outer_padding(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        report = parse_firmware(fixture(payload, outer_pad=2))
        self.assertEqual(report["outer_release_info"]["pad"], 2)

    def test_rejects_outer_length_past_metadata_boundary(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(payload, outer_length_delta=1000))

    def test_rejects_outer_padding_past_metadata_boundary(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(payload, outer_pad=255, include_outer_padding=False))

    def test_rejects_tlv_payload_past_outer_boundary(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(payload, tlv_length_delta=100))

    def test_rejects_zero_region_count(self):
        data = bytearray(fixture(bytes([0x02, 0xC0]) + bytes(14)))
        data[-TRAILER_SIZE + 2] = 0
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(bytes(data))

    def test_rejects_region_descriptor_table_outside_firmware(self):
        data = bytearray(36)
        data[-36 + 2] = 255
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(bytes(data))

    def test_rejects_region_data_overlapping_metadata(self):
        data = bytearray(fixture(bytes([0x02, 0xC0]) + bytes(14)))
        trailer_offset = len(data) - 36
        region_offset = trailer_offset - 40
        struct.pack_into("<I", data, region_offset + 20, region_offset)
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(bytes(data))


    def test_rejects_feature_payload_shorter_than_common_structure(self):
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(b"\\x80\\x00"))

    def test_rejects_missing_feature_tlv(self):
        unknown = struct.pack("<HBB", 3, 0, 1) + b"abc"
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(None, extra_tlvs=(unknown,)))

    def test_rejects_duplicate_feature_tlvs(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        duplicate = struct.pack("<HBB", len(payload), 0, 4) + payload
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(payload, extra_tlvs=(duplicate,)))

    def test_rejects_truncated_tlv_header(self):
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(None, extra_tlvs=(b"\\x01\\x00",)))

    def test_rejects_tlv_padding_past_outer_boundary(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(fixture(payload, tlv_pad=2, include_tlv_padding=False))

    def test_accepts_bounded_tlv_padding_and_unknown_tlv(self):
        payload = bytes([0x02, 0xC0]) + bytes(14)
        unknown = struct.pack("<HBB", 3, 0, 1) + b"abc"
        report = parse_firmware(fixture(payload, tlv_pad=2, extra_tlvs=(unknown,)))
        self.assertEqual([item["tag"] for item in report["tlvs"]], [4, 1])
        self.assertTrue(report["tlvs"][0]["cnm_bit_7"])

    def test_rejects_truncated_firmware(self):
        with self.assertRaises(FirmwareFormatError):
            parse_firmware(b"short")


if __name__ == "__main__":
    unittest.main()
