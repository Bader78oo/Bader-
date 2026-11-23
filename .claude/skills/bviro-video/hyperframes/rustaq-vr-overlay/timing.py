#!/usr/bin/env python3
"""timing.py words.json -> hf/words.js, hf/index.html, build/sb.json  (54 script words with start/end)"""
import json, os, subprocess, sys
w = json.load(open(sys.argv[1], encoding="utf-8")); assert len(w) == 54, len(w)
W = [round(x["s"], 3) for x in w]; E = [round(x["e"], 3) for x in w]
f = lambda t: round(round(t * 30) / 30, 3)
C = {"hook2": f(W[4] - 0.02), "uni": f(W[6] - 0.10), "rus": f(W[11] - 0.08), "last": f(W[13] - 0.08), "in": f(W[21] - 0.10),
     "door": f(W[23] - 0.06), "cls": f(W[25] - 0.06), "stu": f(W[26] - 0.05), "lab": f(W[27] - 0.06), "dig": f(W[32] - 0.10),
     "docs": f(W[38] - 0.10), "tryit": f(W[44] - 0.10), "freeze": f(W[45] - 0.05), "end": f(W[47] - 0.12)}
DUR = f(E[53] + 1.7)
os.makedirs("hf", exist_ok=True); os.makedirs("build", exist_ok=True)
open("hf/words.js", "w").write(f"const W={json.dumps(W)},E={json.dumps(E)},CUT={json.dumps(C)},DUR={DUR};\n")
open("hf/index.html", "w", encoding="utf-8").write(open("py/index.tpl.html", encoding="utf-8").read().replace("__DUR__", str(DUR)))
order = [("v_class.mp4", 0, None), ("r_try.mp4", 2.5, "flash"), ("r_hall.mp4", 0, "zoom"), ("r_watch.mp4", 0, "whip"), ("r_lab.mp4", 0, "zoom"),
         ("v_menu.mp4", 0.3, "flash"), ("v_enter.mp4", 0.0, "zoom"), ("v_table.mp4", 0, "flash"), ("v_students.mp4", 0, "whip"), ("v_lab.mp4", 0, "zoom"),
         ("c_split2.mp4", 0, "flash"), ("r_aud.mp4", 0, "zoom"), ("r_try.mp4", 0, "whip"), ("r_freeze.jpg", None, "flash"), ("v_end.mp4", 0, "flash")]
cuts = [0, C["hook2"], C["uni"], C["rus"], C["last"], C["in"], C["door"], C["cls"], C["stu"], C["lab"], C["dig"], C["docs"], C["tryit"], C["freeze"], C["end"], DUR]
shots = []
for (src, inn, tin), a, b in zip(order, cuts[:-1], cuts[1:]):
    s = {"src": src, "dur": round(b - a, 3)}
    if inn is not None: s["in"] = inn
    if tin: s["tin"] = tin
    if src.endswith(".jpg"): s.update(kb="in", kb_zoom=0.05)
    p = "clips/" + src
    if os.path.exists(p) and not src.endswith(".jpg"):
        L = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
        flag = "" if L - (inn or 0) >= s["dur"] - 0.02 else "   <-- TOO SHORT"
        print(f"{src:16s} need {s['dur']:.2f}  have {L - (inn or 0):.2f}{flag}")
    shots.append(s)
sb = {"width": 1080, "height": 1920, "fps": 30, "duration": DUR, "output": "basegraded.mp4", "shots": shots,
      "transitions": {"default": "zoom"}, "grade": {"lut": "brand/bviro_look.cube", "grain": 4},
      "audio": {"pad": False, "whoosh_on_cuts": False, "impact_at_end": False, "duck": False}}
json.dump(sb, open("build/sb.json", "w"), ensure_ascii=False, indent=1)
print("DUR", DUR, "cuts", C)
