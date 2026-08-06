#!/bin/sh
u="$1"; f="gsprof/$(basename "$u").html"
[ -s "$f" ] || curl -s -L --max-time 30 "$u" -o "$f"
