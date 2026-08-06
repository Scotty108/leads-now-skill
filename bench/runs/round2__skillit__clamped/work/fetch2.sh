#!/bin/sh
u="$1"; f="cmcprof/$(basename "$u").html"
[ -s "$f" ] || curl -s -L --max-time 25 "$u" -o "$f"
