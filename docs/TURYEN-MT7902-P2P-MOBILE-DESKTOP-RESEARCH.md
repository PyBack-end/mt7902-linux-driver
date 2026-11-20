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

The primary target is communication between two separate devices:

- **Desktop:** Linux computer with an MT7902E wireless radio and the experimental MT7902 driver.
- **Mobile:** Turyen mobile application running on a supported phone and its wireless hardware/OS stack.
- **Transport:** Direct peer wireless communication using a validated P2P-capable link, without a conventional router or internet connection as a required intermediary.

The mobile device is a separate peer. It is not the second radio on the same laptop.

The ZT9101 USB adapter is a separate, optional hardware experiment and is not the primary target or required participant in this MT7902E mobile-to-desktop architecture.

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

Evidence should include kernel version, driver revision, firmware identity, interface names, command output, logs, peer device details and failure conditions.

## 8. Security and architectural boundaries

- Do not equate successful radio association with Turyen identity authentication.
- Do not assume P2P provides Turyen's application-level trust or security model.
- Secure application communication and identity verification must be designed and validated separately.
- Do not advertise unsupported driver/firmware capabilities.
- Do not enable CNM or other firmware capabilities through an unconditional override without evidence.
- Do not claim that the MT7902 driver alone enables unrestricted mobile radio control.
- Avoid introducing unrelated transport implementations or rewriting Nearby while investigating driver capabilities.

## 9. Scope exclusions

This stage does not require:

- The ZT9101 USB adapter.
- A router or internet connection for the intended direct-link experiment.
- A full Nearby data-transfer protocol implementation.
- Rewriting the existing BLE foundation.
- Unverified firmware capability overrides.
- A new proprietary RF protocol.

The ZT9101 can be explored independently, but it is not the mobile-to-desktop target defined here.

## 10. Next milestone

Validate the MT7902E's P2P capability and actual connection behavior against a separate peer device, ideally the Turyen mobile device where platform APIs and permissions permit.

Only after this validation should we design the Turyen integration around the demonstrated Linux and mobile platform capabilities.

**The current task is driver-level P2P capability investigation and real-peer validation, with mobile-to-desktop Turyen communication as the end goal.**
