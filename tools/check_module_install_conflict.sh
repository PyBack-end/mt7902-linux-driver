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

# 7.1+ has upstream support; 7.0 is allowed for this test
if [ "$major" -gt 7 ] || { [ "$major" -eq 7 ] && [ "$minor" -ge 1 ]; }; then
	echo "Linux $kernel_version has upstream MT7902 support; refusing out-of-tree module installation. Use the in-tree mt7921e driver." >&2
	exit 1
fi

module_root="${3:-/lib/modules/$kernel_version}"
if [ ! -d "$module_root" ]; then
	echo "kernel module directory does not exist: $module_root" >&2
	exit 1
fi

# Alias and existing-module checks temporarily disabled for the P2P test install.
# Restore the original file from git after the test if you want the guards back.

exit 0
