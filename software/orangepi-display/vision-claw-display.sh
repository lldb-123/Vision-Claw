#!/bin/sh
# Restore the small HDMI panel's tested timing when XFCE resets it.
connector=/sys/class/drm/card0-HDMI-A-1
output=HDMI-1
mode=1024x600_GTF60
panel_edid=521b95fe153a71edd7f151b05813c6555c05d2166812b01e45446811b5f0d598

apply_panel_mode() {
    read -r status < "$connector/status" || return 1
    [ "$status" = connected ] || return 0
    checksum=$(sha256sum "$connector/edid") || return 1
    [ "${checksum%% *}" = "$panel_edid" ] || return 0

    settings=$(xrandr --current --prop) || return 1
    if printf '%s\n' "$settings" | awk -v output="$output" -v mode="$mode" '
        /^[^[:space:]]/ { selected = ($1 == output && $2 == "connected") }
        selected && $1 == "color_format:" && $2 == "rgb" { rgb = 1 }
        selected && $1 == mode && /\*/ { active = 1 }
        END { exit !(rgb && active) }
    '; then
        return 0
    fi

    # The mode may already exist during a hotplug in the same X session.
    xrandr --newmode "$mode" 48.96 1024 1064 1168 1312 600 601 604 622 -HSync +VSync 2>/dev/null || :
    xrandr --addmode "$output" "$mode" || return 1
    xrandr --output "$output" --mode "$mode" --set color_format rgb || return 1
    logger -t vision-claw-display "Applied $mode (RGB) to $output"
}

if [ "${1:-}" = --watch ]; then
    session_pid=$(pgrep -o -u "$(id -u)" -x xfce4-session) || exit 1
    exec 9>"${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/vision-claw-display.lock"
    flock -n 9 || exit 0
    while kill -0 "$session_pid" 2>/dev/null; do
        apply_panel_mode
        sleep 2
    done
else
    apply_panel_mode
fi
