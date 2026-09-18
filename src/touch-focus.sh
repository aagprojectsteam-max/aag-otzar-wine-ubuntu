#!/usr/bin/env bash
set -u
export DISPLAY=:201

while :; do
    W="$(xdotool search --name '^otzar$' 2>/dev/null | tail -1 || true)"
    [ -n "$W" ] && break
    sleep 0.15
done

stdbuf -oL xinput test-xi2 --root 2>/dev/null |
while IFS= read -r LINE; do
    case "$LINE" in
        *"(TouchBegin)"*)
            W="$(xdotool search --name '^otzar$' 2>/dev/null | tail -1 || true)"
            if [ -n "$W" ]; then
                xdotool windowfocus "$W" 2>/dev/null || true
            fi
            ;;
    esac
done
