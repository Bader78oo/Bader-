#!/usr/bin/env python3
"""Hook lab: render only the opening of several hook variants of one reel, score each, compare.

Usage (from the reel's work dir, next to sb.json and its media):
  python3 hook_lab.py sb.json variants.json [--secs 4]

variants.json = [
  {"name": "A_current"},                                              # the storyboard as it is
  {"name": "B_villa", "first_shot": {"src": "v72.mp4", "in": 0.4},    # swap the opening shot (keeps its duration)
  {"name": "C_two_cuts", "open_shots": [{"src": "a.mp4", "in": 0, "dur": 1.8}, {"src": "b.mp4", "in": 0.3, "dur": 1.8, "tin": "zoom"}]},
   "hook": {"text": "…", "sub": "…", "s": 0.1},                        # override the first hook panel
   "sfx_add": [{"t": 0.0, "type": "impact"}]}                          # extra sound at the top
]
Writes hooklab/<name>/hook.mp4 + score.json for each, hooklab/compare.mp4 (side by side, variant voice
on the first one) and hooklab/scores.md (ranked). Nothing is spent: no generation happens here.
"""
import argparse, copy, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("sb"); ap.add_argument("variants"); ap.add_argument("--secs", type=float, default=4.0)
a = ap.parse_args()
base = json.load(open(a.sb, encoding="utf-8")); variants = json.load(open(a.variants, encoding="utf-8"))
N = a.secs; root = os.path.abspath("hooklab"); os.makedirs(root, exist_ok=True)

def trim(sb):
    """Cut a storyboard down to its first N seconds."""
    sb = copy.deepcopy(sb); shots, t = [], 0.0
    for s in sb["shots"]:
        if t >= N - 1e-6: break
        s["dur"] = round(min(s["dur"], N - t), 3); shots.append(s); t += s["dur"]
    sb["shots"], sb["duration"] = shots, N
    for k in ("end_card", "cta", "checklist", "name_card"):
        if sb.get(k) and sb[k]["s"] >= N: sb.pop(k)
    for k in ("captions", "stickers"):
        sb[k] = [dict(x, e=min(x["e"], N)) for x in sb.get(k, []) if x["s"] < N]
    hooks = sb["hook"] if isinstance(sb.get("hook"), list) else ([sb["hook"]] if sb.get("hook") else [])
    sb["hook"] = [dict(h, e=min(h["e"], N)) for h in hooks if h["s"] < N]
    au = sb.setdefault("audio", {})
    au["sfx"] = [e for e in au.get("sfx", []) if e["t"] < N]
    au["impact_at_end"] = False
    return sb

files = {s["src"] for s in base["shots"]} | {s["src"] for v in variants for s in v.get("open_shots", [])} | \
        {v["first_shot"]["src"] for v in variants if v.get("first_shot", {}).get("src")} | {base.get("voiceover"), base.get("words"), base.get("audio", {}).get("music")}
results = []
for v in variants:
    sb = copy.deepcopy(base)
    if v.get("open_shots"):  # replace the first shot by several (their durations should add up to the old one)
        sb["shots"] = v["open_shots"] + sb["shots"][1:]
    if v.get("first_shot"): sb["shots"][0].update(v["first_shot"])
    for k in ("depth", "kb"):
        if v.get("first_shot") and k not in v["first_shot"] and "src" in v["first_shot"]: sb["shots"][0].pop(k, None)
    if v.get("hook"):
        hooks = sb["hook"] if isinstance(sb.get("hook"), list) else [sb["hook"]]
        first = min(range(len(hooks)), key=lambda i: hooks[i]["s"]); hooks[first] = dict(hooks[first], **v["hook"]); sb["hook"] = hooks
    sb.setdefault("audio", {}).setdefault("sfx", []).extend(v.get("sfx_add", []))
    sb = trim(sb); sb["output"] = "hook.mp4"
    d = os.path.join(root, v["name"]); os.makedirs(d, exist_ok=True)
    for f in files | {s["src"] for s in sb["shots"]}:
        if f and os.path.exists(f) and not os.path.exists(os.path.join(d, f)):
            os.symlink(os.path.abspath(f), os.path.join(d, f))
    json.dump(sb, open(os.path.join(d, "sb.json"), "w"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, os.path.join(HERE, "build.py"), "sb.json"], cwd=d, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([sys.executable, os.path.join(HERE, "hook_score.py"), "hook.mp4", "--sb", "sb.json", "--json", "score.json"],
                   cwd=d, check=True)
    results.append((json.load(open(os.path.join(d, "score.json")))["hook_score"], v["name"]))

results.sort(reverse=True)
with open(os.path.join(root, "scores.md"), "w") as f:
    f.write("| rank | variant | hook score |\n|---|---|---|\n")
    for r, (sc, name) in enumerate(results, 1): f.write(f"| {r} | {name} | {sc} |\n")
names = [v["name"] for v in variants]
ins = sum([["-i", os.path.join(root, n, "hook.mp4")] for n in names], [])
lab = ";".join(f"[{i}:v]scale=360:640,setsar=1[v{i}]" for i in range(len(names)))
subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
                lab + ";" + "".join(f"[v{i}]" for i in range(len(names))) + f"hstack=inputs={len(names)}[v]",
                "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-movflags", "+faststart",
                os.path.join(root, "compare.mp4")], check=True)
print(open(os.path.join(root, "scores.md")).read())
