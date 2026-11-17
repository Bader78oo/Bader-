"""PUT local files to the presigned URLs of the most recent Higgsfield media_upload result found in the session transcript.
usage: put_uploads.py TRANSCRIPT.jsonl DIR   (matches by filename in the 'instructions' text)"""
import json, re, subprocess, sys, os
tr, d = sys.argv[1], sys.argv[2]
def find(o):
    if isinstance(o, str):
        if "upload_url" in o:
            try:
                j = json.loads(o)
                if isinstance(j, dict) and "uploads" in j: return j
            except Exception: pass
        return None
    if isinstance(o, dict):
        for v in o.values():
            r = find(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = find(v)
            if r: return r
    return None
res = None
for line in open(tr, encoding="utf-8", errors="replace"):
    if "upload_url" not in line:
        continue
    try:
        r = find(json.loads(line))
    except Exception:
        r = None
    if r: res = r
for u in res["uploads"]:
    m = re.search(r"--data-binary @(\S+)", u["instructions"])
    fn = m.group(1)
    p = os.path.join(d, fn)
    code = subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-X", "PUT", "-H", f"Content-Type: {u['content_type']}",
                           "-H", "If-None-Match: *", "--data-binary", f"@{p}", u["upload_url"]], capture_output=True, text=True).stdout
    print(fn, u["media_id"], code)
