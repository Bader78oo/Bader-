"""Extract the metrics JSON embedded in a Higgsfield Brain Activity Viewer HTML.

usage: python3 -I extract_metrics.py DASHBOARD.html OUT.json
"""
import json
import re
import sys

html = open(sys.argv[1], encoding="utf-8", errors="replace").read()
scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.S)
found = None
for i, s in enumerate(scripts):
    t = s.strip()
    if not t.startswith("{"):
        continue
    try:
        d = json.loads(t)
    except Exception:
        continue
    if isinstance(d, dict) and "scores" in d:
        found = (i, d)
        break
if not found:
    sys.exit("no metrics JSON found; scripts: %s" % [len(s) for s in scripts])
i, d = found
json.dump(d, open(sys.argv[2], "w"), ensure_ascii=False)
print("script index", i, "keys", list(d.keys()))
