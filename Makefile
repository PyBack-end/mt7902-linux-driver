# SPDX-License-Identifier: GPL-2.0-only
KVER ?= $(if $(KERNELRELEASE),$(KERNELRELEASE),$(shell uname -r))
KSRC ?= $(if $(KERNEL_SRC),$(KERNEL_SRC),/lib/modules/$(KVER)/build)
FWDIR := /lib/firmware/mediatek
JOBS ?= $(shell nproc --ignore=1)
MODNAME := mt7902e
MODDESTDIR := /lib/modules/$(KVER)/updates/dkms
MT76DIR := /lib/modules/$(KVER)/kernel/drivers/net/wireless/mediatek/mt76
STAGING_DIR ?= $(CURDIR)/build/stage
INSTALL_MARKER := /var/lib/mt7902e-manual-install
FIRMWARE_MANIFEST := /var/lib/mt7902e-firmware-files

ifneq ("$(INSTALL_MOD_PATH)", "")
DEPMOD_ARGS = -b $(INSTALL_MOD_PATH)
else
DEPMOD_ARGS =
endif

ifneq ("","$(wildcard $(MT76DIR)/*.ko.gz)")
COMPRESS_GZIP := y
endif
ifneq ("","$(wildcard $(MT76DIR)/*.ko.xz)")
COMPRESS_XZ := y
endif
ifneq ("","$(wildcard $(MT76DIR)/*.ko.zst)")
COMPRESS_ZSTD := y
endif

export COMPRESS_GZIP COMPRESS_XZ COMPRESS_ZSTD

SRC_DIR := $(shell pwd)/src

.PHONY: all clean stage install install_fw uninstall uninstall_fw

all:
	$(MAKE) -j$(JOBS) -C $(KSRC) M=$(SRC_DIR) modules
	@cp -v $(SRC_DIR)/*.ko .

clean:
	$(MAKE) -j$(JOBS) -C $(KSRC) M=$(SRC_DIR) clean
	@rm -vf *.ko

# Stage a package tree without changing the host. This is the preferred
# preparation path for review and packaging.
stage: all
	@install -vDm 644 -t "$(STAGING_DIR)/lib/modules/$(KVER)/updates/dkms" *.ko
	@install -vDm 644 -t "$(STAGING_DIR)/lib/firmware/mediatek" firmware/*.bin

# Manual module-file installation is deliberately separate from module
# activation. It never unloads, reloads, or modprobes the running driver.
install: all
	@test "$(ALLOW_SYSTEM_INSTALL)" = "1" || { echo "Refusing system modification; set ALLOW_SYSTEM_INSTALL=1 explicitly."; exit 1; }
	@test "$$(id -u)" -eq 0 || { echo "Run this target as root."; exit 1; }
	@test ! -e "$(INSTALL_MARKER)" && test ! -L "$(INSTALL_MARKER)" || { echo "A manual install marker already exists; inspect it before proceeding."; exit 1; }
	@test ! -e "$(MODDESTDIR)/$(MODNAME).ko" && test ! -L "$(MODDESTDIR)/$(MODNAME).ko" && \
		test ! -e "$(MODDESTDIR)/$(MODNAME).ko.gz" && test ! -L "$(MODDESTDIR)/$(MODNAME).ko.gz" && \
		test ! -e "$(MODDESTDIR)/$(MODNAME).ko.xz" && test ! -L "$(MODDESTDIR)/$(MODNAME).ko.xz" && \
		test ! -e "$(MODDESTDIR)/$(MODNAME).ko.zst" && test ! -L "$(MODDESTDIR)/$(MODNAME).ko.zst" || \
		{ echo "A module already exists in $(MODDESTDIR); refusing to overwrite it."; exit 1; }
	@printf "Type INSTALL MT7902E MODULE FILES to continue: "; read -r answer; test "$$answer" = "INSTALL MT7902E MODULE FILES" || { echo "Confirmation did not match."; exit 1; }
	@install -vDm 644 -t "$(MODDESTDIR)" *.ko
ifeq ($(COMPRESS_GZIP), y)
	@gzip -f "$(MODDESTDIR)"/*.ko
endif
ifeq ($(COMPRESS_XZ), y)
	@xz -f -C crc32 "$(MODDESTDIR)"/*.ko
endif
ifeq ($(COMPRESS_ZSTD), y)
	@zstd -f -q --rm "$(MODDESTDIR)"/*.ko
endif
	@install -d -m 755 /var/lib
	@module_file=$$(find "$(MODDESTDIR)" -maxdepth 1 -type f -name "$(MODNAME).ko*" -print -quit); \
		test -n "$$module_file" || { echo "Installed module file was not found."; exit 1; }; \
		module_hash=$$(sha256sum "$$module_file" | awk '{print $$1}'); \
		printf '%s %s\n' "$$(basename "$$module_file")" "$$module_hash" > "$(INSTALL_MARKER)"
	@depmod $(DEPMOD_ARGS) -a $(KVER)
	@echo "Module files installed. The running driver was NOT changed; reboot or a separately authorized activation is required."

# Firmware is never overwritten. Existing distribution firmware must be
# reviewed and backed up separately before any replacement is considered.
install_fw:
	@test "$(ALLOW_FIRMWARE_INSTALL)" = "1" || { echo "Refusing firmware installation; set ALLOW_FIRMWARE_INSTALL=1 explicitly."; exit 1; }
	@test "$$(id -u)" -eq 0 || { echo "Run this target as root."; exit 1; }
	@test ! -e "$(FIRMWARE_MANIFEST)" && test ! -L "$(FIRMWARE_MANIFEST)" || { echo "Firmware manifest already exists; inspect it before proceeding."; exit 1; }
	@test ! -e "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin" && test ! -L "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin" && \
		test ! -e "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin.zst" && test ! -L "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin.zst" && \
		test ! -e "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin.xz" && test ! -L "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin.xz" && \
		test ! -e "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin.gz" && test ! -L "$(FWDIR)/WIFI_MT7902_patch_mcu_1_1_hdr.bin.gz" && \
		test ! -e "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin" && test ! -L "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin" && \
		test ! -e "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin.zst" && test ! -L "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin.zst" && \
		test ! -e "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin.xz" && test ! -L "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin.xz" && \
		test ! -e "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin.gz" && test ! -L "$(FWDIR)/WIFI_RAM_CODE_MT7902_1.bin.gz" || \
		{ echo "Refusing to overwrite existing MT7902 firmware or compressed variant."; exit 1; }
	@printf "Type INSTALL MT7902 FIRMWARE to continue: "; read -r answer; test "$$answer" = "INSTALL MT7902 FIRMWARE" || { echo "Confirmation did not match."; exit 1; }
	@install -vDm 644 -t "$(FWDIR)" firmware/*.bin
	@install -d -m 755 /var/lib
	@for name in WIFI_MT7902_patch_mcu_1_1_hdr.bin WIFI_RAM_CODE_MT7902_1.bin; do \
		sha256sum "$(FWDIR)/$$name" | awk -v name="$$name" '{print $$1, name}'; \
	done > "$(FIRMWARE_MANIFEST)"

uninstall:
	@test "$(ALLOW_SYSTEM_INSTALL)" = "1" || { echo "Refusing system modification; set ALLOW_SYSTEM_INSTALL=1 explicitly."; exit 1; }
	@test "$$(id -u)" -eq 0 || { echo "Run this target as root."; exit 1; }
	@test -f "$(INSTALL_MARKER)" && test ! -L "$(INSTALL_MARKER)" || { echo "No regular manual-install marker found; refusing to remove untracked module files."; exit 1; }
	@printf "Type REMOVE MT7902E MODULE FILES to continue: "; read -r answer; test "$$answer" = "REMOVE MT7902E MODULE FILES" || { echo "Confirmation did not match."; exit 1; }
	@read -r module_file expected_hash < "$(INSTALL_MARKER)"; \
		case "$$module_file" in "$(MODNAME).ko"|"$(MODNAME).ko.gz"|"$(MODNAME).ko.xz"|"$(MODNAME).ko.zst") ;; *) echo "Invalid install marker; refusing removal."; exit 1 ;; esac; \
		test -f "$(MODDESTDIR)/$$module_file" || { echo "Installed module file is missing; refusing removal."; exit 1; }; \
		actual_hash=$$(sha256sum "$(MODDESTDIR)/$$module_file" | awk '{print $$1}'); \
		test "$$actual_hash" = "$$expected_hash" || { echo "Module file changed since installation; refusing removal."; exit 1; }; \
		rm -f "$(MODDESTDIR)/$$module_file"; \
		rmdir "$(MODDESTDIR)" 2>/dev/null || true; \
		rm -f "$(INSTALL_MARKER)"
	@depmod $(DEPMOD_ARGS) -a $(KVER)
	@echo "Installed module files removed. No module was unloaded; the running driver is unchanged until a later activation/reboot."

uninstall_fw:
	@test "$(ALLOW_FIRMWARE_REMOVAL)" = "1" || { echo "Refusing firmware removal; set ALLOW_FIRMWARE_REMOVAL=1 explicitly."; exit 1; }
	@test "$$(id -u)" -eq 0 || { echo "Run this target as root."; exit 1; }
	@test -f "$(FIRMWARE_MANIFEST)" && test ! -L "$(FIRMWARE_MANIFEST)" || { echo "No regular firmware manifest found; refusing to remove distribution or untracked firmware."; exit 1; }
	@printf "Type REMOVE MT7902 FIRMWARE to continue: "; read -r answer; test "$$answer" = "REMOVE MT7902 FIRMWARE" || { echo "Confirmation did not match."; exit 1; }
	@while read -r expected_hash name; do \
		case "$$name" in \
			WIFI_MT7902_patch_mcu_1_1_hdr.bin|WIFI_RAM_CODE_MT7902_1.bin) ;; \
			*) echo "Unexpected firmware manifest entry: $$name"; exit 1 ;; \
		esac; \
		test -f "$(FWDIR)/$$name" || { echo "Tracked firmware file is missing: $$name"; exit 1; }; \
		actual_hash=$$(sha256sum "$(FWDIR)/$$name" | awk '{print $$1}'); \
		test "$$actual_hash" = "$$expected_hash" || { echo "Firmware file changed since installation: $$name"; exit 1; }; \
	done < "$(FIRMWARE_MANIFEST)"
	@while read -r expected_hash name; do rm -f "$(FWDIR)/$$name"; done < "$(FIRMWARE_MANIFEST)"
	@rm -f "$(FIRMWARE_MANIFEST)"
