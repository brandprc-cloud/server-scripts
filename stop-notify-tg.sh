#!/bin/sh
python3 << 'EOF'
import urllib.request, urllib.parse, json as j
tok = '8932583755:AAFcANi4ekDfLHYRlSAeBxz0U5aTNcQ8MSI'
cid = '6061411038'
base = 'https://api.telegram.org/bot' + tok + '/'
r = urllib.request.urlopen(base + 'sendMessage', urllib.parse.urlencode({'chat_id': cid, 'text': chr(0x1F514)}).encode(), timeout=5)
mid = j.loads(r.read())['result']['message_id']
urllib.request.urlopen(base + 'deleteMessage', urllib.parse.urlencode({'chat_id': cid, 'message_id': mid}).encode(), timeout=5)
EOF
