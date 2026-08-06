#!/bin/bash
# $1=last  $2=first  $3=outfile
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
J=$(mktemp); P=$(mktemp)
curl -sS -L --max-time 30 -A "$UA" -c "$J" -b "$J" "https://portal.ncmedboard.org/verification/search.aspx" -o "$P"
python3 - "$P" > "$P.form" <<'PY'
import re,sys,urllib.parse
h=open(sys.argv[1],encoding='utf-8',errors='replace').read()
d={}
for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>',h,re.I):
    s=m.group(0)
    n=re.search(r'name="([^"]+)"',s); v=re.search(r'value="([^"]*)"',s)
    if n: d[n.group(1)]=v.group(1) if v else ''
print("\n".join("%s=%s"%(k,urllib.parse.quote(v,safe='')) for k,v in d.items()))
PY
BODY=$(tr '\n' '&' < "$P.form")
BODY="${BODY}ctl00%24Content%24txtFirst=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$2")"
BODY="${BODY}&ctl00%24Content%24txtLast=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1")"
BODY="${BODY}&ctl00%24Content%24txtCity=&ctl00%24Content%24txtLicNum=&ctl00%24Content%24ddState=&ctl00%24Content%24ddLicStatus=&ctl00%24Content%24btnSubmit=Search"
curl -sS -L --max-time 40 -A "$UA" -b "$J" -c "$J" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: https://portal.ncmedboard.org/verification/search.aspx" \
  --data-raw "$BODY" \
  "https://portal.ncmedboard.org/verification/search.aspx" -o "$3"
rm -f "$J" "$P" "$P.form"
echo "$3 $(wc -c < "$3")"
