# mt7902e

> [!WARNING]
> This repo is now archived, better support (for kernel 6.12+) is in [morrownr's repo](https://github.com/morrownr/mt76).

This is basically the mainline version of mt76 with [patches to support MT7902](https://lore.kernel.org/all/20260219004007.19733-1-sean.wang@kernel.org/) & firmware provided by Mediatek. I also stripped down all the unnecessary files & other hardware support to ensure only MT7902 card is supported.

> [!CAUTION]
> [Kernel 7.1](https://kernel.org/) has added official support for MT7902 bluetooth and wifi, it's recommended to use their official driver instead and **follow the instructions clearly** on [bugzilla.kernel.org](https://bugzilla.kernel.org/)'s homepage when reporting problems.

> [!WARNING]
> This out-of-tree driver only support the PCIe version of MT7902, for SDIO support it's better if you just merge Mediatek patches on your own !

> [!TIP]
> For Bluetooth support, check out [this branch](https://github.com/hmtheboy154/mt7902/tree/bluetooth_backport).


## Status

The driver supports kernel 6.6~6.19 (and might be 7.0 soon) and is usable according to users reported in this [spreadsheet](https://docs.google.com/spreadsheets/d/1G2mQEeLQAu4oB85G-y4A9OduA1ZP0rUcY-b6MRnZhFU/edit?usp=drive_link&pli=1&authuser=0). 

## Installation

> [!IMPORTANT]
> Before building & installing this driver, remember to install essential packages to build a kernel driver like linux kernel's headers & toolchain. I will not cover it here.

- Get the source using `git`

```bash
git clone https://github.com/hmtheboy154/mt7902
cd mt7902
```

- To only build the driver, use this command

```bash
make -j$(nproc)
```

- To stage the module and firmware into a reviewable package tree without
  changing the host:

```bash
make stage KVER="$(uname -r)" KSRC="/lib/modules/$(uname -r)/build"
```

- Manual module-file installation is guarded and does not activate or reload
  the running driver. It installs only into `updates/dkms`, refuses to
  shadow or replace any existing module for the selected kernel, and requires both an explicit make
  variable and an interactive confirmation:

```bash
sudo make install ALLOW_SYSTEM_INSTALL=1 KVER="$(uname -r)" KSRC="/lib/modules/$(uname -r)/build"
```

The confirmation phrase is `INSTALL MT7902E MODULE FILES`. The preflight also
refuses installation on Linux 7.1 and newer, where MT7902 is supported by the
in-tree `mt7921e` driver. The module remains inactive until a separate
activation/reboot decision. No `modprobe`,
`rmmod`, module unload, or reload is performed by this target.

- Firmware installation is separate, requires
  `ALLOW_FIRMWARE_INSTALL=1` and confirmation phrase
  `INSTALL MT7902 FIRMWARE`, and refuses to overwrite an existing firmware
  file or compressed variant:

```bash
sudo make install_fw ALLOW_FIRMWARE_INSTALL=1
```

Firmware removal is also separate and only removes unchanged files recorded in
the installation manifest. It requires `ALLOW_FIRMWARE_REMOVAL=1` and the
confirmation phrase `REMOVE MT7902 FIRMWARE`:

```bash
sudo make uninstall_fw ALLOW_FIRMWARE_REMOVAL=1
```

> [!TIP]
> As per the [20260309](https://gitlab.com/kernel-firmware/linux-firmware#linux-firmware) release, the firmware should be already provided by your distribution, for Debian as of present, check in the unstable repo.

- To remove module files installed by this Makefile (the running module is
  never unloaded):

```bash
sudo make uninstall ALLOW_SYSTEM_INSTALL=1
```

The confirmation phrase is `REMOVE MT7902E MODULE FILES`. Removal verifies
the recorded SHA-256 before deleting the exact installed module file. It does
not unload the active driver; a reboot or separately authorized transition is
still required.

The installed module files are not activated immediately. Plan any reboot or
module transition separately, with an alternate network path and a recovery
plan available.

## Feedback

If you have any issue using this driver, please provide feedback in this [Discord group](https://discord.gg/JGhjAxEFhz).


## Development notes

- [MT7902 P2P capability investigation](docs/MT7902-P2P-CAPABILITY-INVESTIGATION.md)
- [Firmware metadata inspector](tools/inspect_firmware.py)

The upstream snapshot used by this repository is archived. Review the investigation document before using this source as a long-term driver fallback. Do not force CNM capability based only on firmware metadata or another chipset's behaviour.
