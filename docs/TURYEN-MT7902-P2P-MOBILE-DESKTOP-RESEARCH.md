# Turyen MT7902 P2P: Mobile-to-Desktop Radio Transport Research

**Status:** Active driver research and hardware validation  
**Repository:** `PyBack-end/mt7902-linux-driver`  
**Purpose:** Investigate and validate MT7902 P2P capabilities for Turyen Nearby mobile-to-desktop communication  
**Last updated:** 2026-11-20

## 1. Objective and clarification

The objective is to enable Turyen to use the MT7902E radio as a foundation for direct peer-to-peer (P2P) communication between a Turyen mobile device and a Turyen desktop.

We are fixing, inspecting and experimentally extending the MT7902 Linux driver and its advertised wireless capabilities so Turyen can investigate a direct wireless link that it can coordinate and use, rather than depending on the device operating system's existing Wi-Fi Direct UI/workflow as the product-level connection mechanism.

This does **not** mean we are inventing a new RF protocol or bypassing the radio firmware. We are investigating the driver's P2P support and the standard Linux wireless control/data interfaces, and determining what the radio, firmware, kernel and userspace stack can actually support.

The long-term product objective is mobile and desktop Turyen peers communicating over a direct wireless link, coordinated by Turyen.

## 2. Intended topology

The primary product target is communication between two separate devices:

- **Desktop:** Linux computer with an MT7902E wireless radio and the experimental MT7902 driver.
- **Mobile:** Turyen mobile application running on a supported phone and its wireless hardware/OS stack.
- **Transport:** Direct peer wireless communication using a validated P2P-capable link, without a conventional router or internet connection as a required intermediary.

The mobile device is a separate peer. It is not the second radio on the same laptop.

### 2.1 Preliminary desktop-local adapter experiment

Before Android/mobile interoperability testing, we are conducting a separate, preliminary hardware experiment on the Ubuntu desktop using the ZT9101 USB Wi-Fi adapter alongside the desktop's internal MT7902E radio.

This is a **two-radio, same-host laboratory test**, not the final mobile-to-desktop topology:

- **Radio A:** Internal MT7902E PCIe adapter, currently exposed as `wlp1s0` and bound to the `mt7902e` driver.
- **Radio B:** ZTopInc ZT9101 USB adapter, USB ID `350b:9101`.
- **Host:** Ubuntu desktop `V0id`.
- **Purpose:** Identify the USB adapter's driver and P2P capabilities, determine whether both radios can be initialized for the intended test, and use the two radios as separate radio endpoints if their drivers and firmware support the required P2P operations.

A successful same-host two-radio test can validate parts of the Linux P2P path, but it does **not** prove interoperability with Android or another independent device. Host networking, routing and interface configuration must be controlled so that a local software path is not mistaken for wireless peer communication.

The ZT9101 experiment is independent of the MT7902E driver investigation. It must not be used as evidence that the MT7902E itself supports a capability unless the MT7902E is the radio actually performing that operation.

## 3. Why we are fixing the MT7902 driver

The MT7902 driver work is investigating the gap between advertised wireless interface modes and the underlying P2P concurrency/channel-management capabilities.

The repository's existing investigation documents:

- Firmware feature parsing and CNM capability reporting.
- The channel-context and remain-on-channel (ROC) callback gates.
- Existing host-side ROC command plumbing.
- Unverified firmware capability interpretation.
- A non-CNM same-channel interface-combination advertisement added in November 2026.

The same-channel advertisement change is additive. It does not establish that P2P negotiation, ROC, group lifecycle, or mobile interoperability are proven. Those remain runtime validation tasks.

Repository investigation:
- `docs/MT7902-P2P-CAPABILITY-INVESTIGATION.md`

## 4. Product-level objective

Turyen Nearby should eventually be able to coordinate a direct mobile-to-desktop connection and use that link for peer communication.

Potential future responsibilities include:

- Peer discovery and identification.
- Connection coordination and negotiation.
- Establishment and maintenance of the direct link.
- Secure communication after peer authentication.
- Data transfer.
- Reconnection and link lifecycle management.

These are future integration responsibilities. This driver repository's current work is to establish evidence for the radio and driver capabilities needed by the transport.

## 5. What "not relying on the device Wi-Fi Direct" means

The product goal is not to make users manually navigate the phone's or desktop's Wi-Fi Direct menus and treat that UI as the Turyen experience.

Turyen should coordinate the connection from its own Nearby workflow, subject to the capabilities and restrictions of each platform.

However, the project must not assume that mobile platforms permit arbitrary low-level radio control. On Android, connection setup, P2P operations, permissions and interface access are subject to Android APIs, OS policy and hardware support. On Linux, the driver, firmware, cfg80211/mac80211/nl80211 stack and userspace control components all affect what is possible.

We must establish a practical supported path on both ends. Driver capability alone cannot guarantee mobile interoperability.

## 6. Current research focus in this repository

Keep this repository focused on the MT7902 driver and kernel wireless capability investigation:

1. Review the MT7902 firmware feature metadata and parser.
2. Understand CNM, channel-context, interface-combination and ROC capability gates.
3. Investigate the single-channel P2P concurrency path without falsely asserting unsupported capabilities.
4. Build and test the driver against the target kernel.
5. Validate interface creation and P2P operations on the actual MT7902 hardware.
6. Capture logs, firmware identity, kernel version and reproducible commands.
7. Test discovery, negotiation and group lifecycle with a separate peer device where possible.
8. Determine whether the resulting link can be used by Turyen on the desktop side.
9. Document mobile-side constraints and interoperability findings before proposing integration.

The ZT9101 USB adapter's driver and P2P capability investigation is a separate supporting experiment. Keep its results clearly attributed to the USB adapter and do not merge them with MT7902E capability claims.

## 7. Experimental stages and evidence

Track results by stage; do not claim a later stage from an earlier one.

1. **Source:** Relevant code paths reviewed.
2. **Build:** Driver builds for the target kernel.
3. **Load:** Driver and firmware load successfully; hardware remains stable.
4. **Capability:** Interface modes and combinations are accurately reported.
5. **Operation:** P2P-related operations such as discovery, negotiation and channel handling succeed as supported.
6. **Peer:** A separate mobile or other peer is discovered and a connection/group is negotiated.
7. **Communication:** Data exchange across the actual wireless link is demonstrated, with the test excluding host-local routing or other false positives.
8. **Turyen integration:** Turyen can coordinate and use the validated transport on the relevant platforms.

### 7.1 Desktop-local two-radio test: ZT9101 + MT7902E

This test is a preliminary step before Android/desktop testing. Its purpose is to determine whether the external USB adapter can serve as a second P2P radio endpoint alongside the internal desktop radio.

**Initial hardware snapshot (2026-11-20):**

| Item | Observed result |
|---|---|
| Host | Ubuntu desktop `V0id` |
| USB adapter | ZTopInc 802.11n NIC, USB ID `350b:9101` |
| USB adapter kernel network interface | Not present in `ip -br link` |
| USB adapter wireless PHY | Not present in `iw dev` / reported `iw phy` output |
| Internal radio | MT7902E PCIe, interface `wlp1s0` |
| Internal radio driver | `mt7902e` |
| Internal radio P2P modes reported by cfg80211 | `P2P-client`, `P2P-GO`, `P2P-device` |
| Internal radio P2P-device initialization | Failed in the captured wpa_supplicant startup logs |

**Evidence and interpretation:**

- `lsusb` detects the ZT9101 as `350b:9101 ZTopInc 802.11n NIC`.
- `ip -br link` lists `wlp1s0` but no interface corresponding to the ZT9101.
- The network-interface driver inspection shows `wlp1s0` bound to `/sys/bus/pci/drivers/mt7902e`. No USB Wi-Fi network interface is present in that snapshot.
- `iw dev` reports only `phy#0` / `wlp1s0`.
- The displayed `iw phy` capability report is for `phy0`, the internal MT7902E. It advertises `P2P-client`, `P2P-GO`, `P2P-device` and the `start_p2p_device` command. These advertised modes do not prove successful P2P operation.
- The attempted command `sudo iw phy PHY_NAME info` failed with `No such file or directory (-2)` because `PHY_NAME` was a placeholder, not an actual PHY identifier. No ZT9101 PHY name has been established yet.
- NetworkManager 1.54.3 creates a logical `p2p-dev-wlp1s0` device for the internal radio. The supplicant startup log reports `Could not set interface 'p2p-dev-wlp1s0' UP`, `Failed to initialize driver interface` and `P2P: Failed to enable P2P Device interface`. A later `P2P_FIND` command is rejected because P2P is disabled. This is an MT7902E P2P initialization failure in the captured run; it is not evidence of a ZT9101 failure.
- The ZT9101 is currently detected at the USB layer but has not been shown to bind to a working wireless driver or expose a wireless PHY. Its P2P capability is therefore **unknown / unverified**.

**Next actions:**

1. Identify the ZT9101 USB interface binding, candidate driver, kernel messages and firmware requirements.
2. Establish whether the ZT9101 creates a network interface and wireless PHY.
3. Query the actual ZT9101 PHY by its discovered name with `iw phy <actual-phy-name> info`; do not use a placeholder literally.
4. Record its supported interface modes, supported commands, valid interface combinations, channel limits and relevant driver/firmware details.
5. Independently diagnose the MT7902E P2P-device initialization failure. Do not infer that P2P is enabled merely because the kernel advertises P2P modes.
6. Once both radios expose usable interfaces, test P2P device initialization and discovery, then group negotiation between the two radios if the drivers support it.
7. Verify the resulting data path between the two wireless interfaces and rule out local routing or other host-local shortcuts.
8. Record results separately for the ZT9101 and MT7902E, including which radio performs each operation.

**Current result:** USB enumeration of the ZT9101 is confirmed. USB network-interface creation, driver binding, wireless PHY exposure, P2P capability, P2P discovery, group formation and data transfer are **not yet demonstrated**.

A same-host two-radio test is only a laboratory validation step. After it, repeat the relevant tests with a genuinely separate peer, preferably the Turyen Android device, to establish mobile-to-desktop interoperability.

Evidence should include kernel version, driver revision, firmware identity, interface names, command output, logs, peer device details and failure conditions.

## 8. Security and architectural boundaries

- Do not equate successful radio association with Turyen identity authentication.
- Do not assume P2P provides Turyen's application-level trust or security model.
- Secure application communication and identity verification must be designed and validated separately.
- Do not advertise unsupported driver/firmware capabilities.
- Do not enable CNM or other firmware capabilities through an unconditional override without evidence.
- Do not claim that the MT7902 driver alone enables unrestricted mobile radio control.
- Avoid introducing unrelated transport implementations or rewriting Nearby while investigating driver capabilities.
- Keep evidence from the ZT9101 USB adapter separate from evidence about the MT7902E.

## 9. Scope exclusions

This stage does not require:

- A router or internet connection for the intended direct-link experiment.
- A full Nearby data-transfer protocol implementation.
- Rewriting the existing BLE foundation.
- Unverified firmware capability overrides.
- A new proprietary RF protocol.

The ZT9101 is not part of the primary MT7902E mobile-to-desktop product architecture. It is being used as a separate preliminary desktop-local hardware experiment before Android/desktop interoperability testing.

## 10. Next milestone

First, identify and bring up the ZT9101 USB adapter sufficiently to establish its actual driver, wireless PHY and P2P capabilities. In parallel, diagnose the MT7902E P2P-device initialization failure. If both radios can support the required operations, perform the desktop-local two-radio discovery, group-formation and data-path tests, keeping each radio's evidence distinct.

Then validate the MT7902E's P2P capability and actual connection behavior against a separate peer device, ideally the Turyen mobile device where platform APIs and permissions permit.

Only after this validation should we design the Turyen integration around the demonstrated Linux and mobile platform capabilities.

**The current task is driver-level P2P capability investigation and real-peer validation, with mobile-to-desktop Turyen communication as the end goal.**
