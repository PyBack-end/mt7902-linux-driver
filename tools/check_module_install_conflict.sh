#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
	echo "usage: check_module_install_conflict.sh KVER MODNAME" >&2
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

module_root="/lib/modules/$kernel_version"
if [ ! -d "$module_root" ]; then
	echo "kernel module directory does not exist: $module_root" >&2
	exit 1
fi

existing_module="$(find "$module_root" \( -type f -o -type l \) \(
	-name "$module_name.ko" -o
	-name "$module_name.ko.gz" -o
	-name "$module_name.ko.xz" -o
	-name "$module_name.ko.zst"
\) -print -quit 2>/dev/null || true)"

if [ -n "$existing_module" ]; then
	echo "An existing $module_name module was found at $existing_module; refusing to shadow or replace it." >&2
	exit 1
fi

exit 0
