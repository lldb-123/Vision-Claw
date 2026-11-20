#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
program="$HOME/.local/bin/vision-claw-display.sh"
autostart="$HOME/.config/autostart/vision-claw-display.desktop"

install -Dm755 "$script_dir/vision-claw-display.sh" "$program"
mkdir -p "$(dirname -- "$autostart")"
cat > "$autostart" <<EOF
[Desktop Entry]
Type=Application
Name=Vision-Claw small HDMI display
Exec="$program" --watch
OnlyShowIn=XFCE;
StartupNotify=false
Terminal=false
EOF

printf '%s\n' 'Display setup installed. The watcher starts at the next XFCE login.'
