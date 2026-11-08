# MT7902 P2P capability investigation

## Scope

This work investigates why the MT7902 driver advertises P2P interface types but
does not expose the full P2P interface-combination and remain-on-channel path
when the firmware capability parser does not report CNM.

## Driver source provenance

The original upstream snapshot used for this repository is archived. Before
using it as a long-term fallback, compare it with the actively maintained
[morrownr/mt76 project](https://github.com/morrownr/mt76), which lists MT7902
support and newer kernel coverage. This is a candidate for source review, not
an automatic replacement: P2P/ROC behaviour must still be verified against the
actual firmware and target hardware. Its current installer also installs a
modprobe configuration that blacklists several in-kernel mt76 modules, so it
must not be invoked as a Turyen per-device fallback without redesigning that
installation policy.

## Confirmed source-level behaviour

- The shared MT792x firmware feature structure is 16 bytes: segment, data, and
  14 reserved bytes.
- The parser extracts the offload capability byte from the feature TLV data.
- The shared core gates remain-on-channel callbacks and the channel-context
  interface-combination table on MT792x_FW_CAP_CNM.
- A comparison against the current actively maintained `morrownr/mt76` source
  found a firmware-name-specific runtime CNM override for MT7927, but no
  equivalent MT7902 override. This is not proof that MT7902 cannot support CNM;
  it is evidence that the maintained driver does not currently assert it.
- The inspected MT7902 RAM firmware has a 36-byte feature TLV, with segment
  0x80 and data 0x00. Its CNM bit is therefore not set by the current parser.
- MT7922, MT7961 and MT7925 comparison firmware inspected during this work
  use 16-byte feature TLVs and set the CNM bit.

## Host-side ROC implementation

The MT7902 tree inherits the MT7921 mac80211 ROC callbacks from `mt7902/main.c`.
Its MCU layer contains ROC acquire/abort request construction using
`MCU_UNI_CMD(ROC)` and handles `MCU_UNI_EVENT_ROC` grants. The shared core still
removes the callbacks when CNM is absent. This establishes that host-side command
plumbing exists; it does not establish that MT7902 firmware accepts the command,
returns a grant, or safely supports the channel-context lifecycle.

## Hypotheses that remain unproven

1. The MT7902 feature TLV may contain a chipset-specific extension after the
   common 16-byte feature structure.
2. Segment 0x80 may describe a different firmware capability layout or segment
   selection; its meaning must be confirmed from firmware format definitions
   or controlled firmware/driver traces.
3. MT7902 may not implement the complete CNM command set even if the metadata
   could be interpreted to indicate support.
4. The lack of CNM may be intentional firmware policy rather than a parser bug.

## Firmware inspection tooling

`tools/inspect_firmware.py` reads a firmware image and validates the trailer,
region descriptor bounds, outer release-info block and nested TLV boundaries.
It reports the common 16-byte feature structure and preserves any bytes beyond
that structure as uninterpreted hexadecimal data. It deliberately does not
assign semantics to the MT7902-specific 20-byte extension.

Run its regression tests with:

```bash
python3 -m unittest discover -s tools -p 'test_*.py' -v
```

Inspect a firmware image with:

```bash
python3 tools/inspect_firmware.py firmware/WIFI_RAM_CODE_MT7902_1.bin
```

## Required evidence before changing runtime capability behaviour

- Identify the meaning of all 36 bytes in the MT7902 feature TLV.
- Trace the exact MCU commands used by CNM, channel contexts and ROC.
- Compare MT7902 command/event handling with supported Connac2 chipsets.
- Confirm firmware responses and error codes for each command.
- Verify mac80211 callbacks and interface combinations against the actual
  firmware command support.
- Add parser fixtures for all known firmware layouts.
- Keep firmware parsing hardening independent from any CNM override.

## Non-goals

- Do not unconditionally set MT792x_FW_CAP_CNM for MT7902.
- Do not advertise P2P concurrency based only on interface mode bits.
- Do not change firmware blobs or install a module as part of investigation.
- Do not use a different chipset's firmware as a substitute.

## Existing parser hardening

The firmware bounds-validation work remains isolated in PR #1. It should be
reviewed and merged independently of capability-behaviour changes.

## Acceptance levels

1. Static: parser and command-path code reviewed.
2. Build: driver compiles against target kernel headers.
3. Runtime: firmware loads and device remains stable.
4. Capability: P2P discovery and ROC operations succeed.
5. Integration: Turyen forms a group and transfers authenticated data.

Passing a lower level does not imply passing a higher one.
