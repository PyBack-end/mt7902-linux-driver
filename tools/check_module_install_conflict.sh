#!/bin/sh
set -eu

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
	echo "usage: check_module_install_conflict.sh KVER MODNAME [MODULE_ROOT]" >&2
	exit 2
fi

kernel_version=$1
module_name=$2

case "$kernel_version" in
	""|*/*|*..*) echo "invalid kernel version" >&2; exit 2 ;;
esac
case "$module_name" in
	""|*[!A-Za-z0-9_-]*) echo "invalid module name" >&2; exit 2 ;;
esac

version_prefix=${kernel_version%%-*}
case "$version_prefix" in
	*.*) ;;
	*) echo "invalid kernel version" >&2; exit 2 ;;
esac
major=${version_prefix%%.*}
version_rest=${version_prefix#*.}
minor=${version_rest%%.*}
case "$major:$minor" in
	*[!0-9:]*|:*) echo "invalid kernel version" >&2; exit 2 ;;
esac
if [ "$major" -gt 7 ] || { [ "$major" -eq 7 ] && [ "$minor" -ge 1 ]; }; then
	echo "Linux $kernel_version has upstream MT7902 support; refusing out-of-tree module installation. Use the in-tree mt7921e driver." >&2
	exit 1
fi

module_root="${3:-/lib/modules/$kernel_version}"
if [ ! -d "$module_root" ]; then
	echo "kernel module directory does not exist: $module_root" >&2
	exit 1
fi

if [ -f "$module_root/modules.alias" ] && grep -Eiq '^alias pci:v000014C3d00007902.*[[:space:]]mt7921e$' "$module_root/modules.alias"; then
	echo "The selected kernel already has an MT7902 PCI alias in mt7921e; refusing to install a competing driver." >&2
	exit 1
fi

existing_module="$(find "$module_root" \( -type f -o -type l \) \( -name "$module_name.ko" -o -name "$module_name.ko.gz" -o -name "$module_name.ko.xz" -o -name "$module_name.ko.zst" \) -print -quit 2>/dev/null || true)"

if [ -n "$existing_module" ]; then
	echo "An existing $module_name module was found at $existing_module; refusing to shadow or replace it." >&2
	exit 1
fi

exit 0
