#!/bin/bash
input=$(cat)

python3 -c "
import json, sys

try:
    data = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)

parts = []

rl = data.get('rate_limits', {})
five = rl.get('five_hour', {}).get('used_percentage')
week = rl.get('seven_day', {}).get('used_percentage')

if five is not None:
    remaining = round(100 - float(five))
    parts.append(f'5h: {remaining}%')

if week is not None:
    remaining = round(100 - float(week))
    parts.append(f'7d: {remaining}%')

cwd = data.get('cwd') or (data.get('workspace') or {}).get('current_dir', '')
if cwd:
    folder = cwd.rstrip('/').split('/')[-1] or cwd
    parts.append(folder)

print(' | '.join(parts), end='')
" "$input"
