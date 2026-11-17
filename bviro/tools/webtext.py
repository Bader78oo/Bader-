"""Read a public web page through the session proxy and print its readable text.
usage: python3 -I webtext.py URL [--grep REGEX] [--max N] [--raw]
One plain request with a generic client name. If the site answers with an error or an empty shell, that is reported
as it is: this tool does not try to get around a site's refusal.
Prints: final URL, HTTP code, title, publication dates found in meta tags / JSON-LD / <time>, then the text
(or only the passages around --grep matches). --raw searches the raw HTML instead of the extracted text."""
import html, re, subprocess, sys

UA = "research-client/1.0"


def text_of(s):
    t = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", s)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h[1-6]>|</tr>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def dates(s):
    found = []
    for pat in (r'"datePublished"\s*:\s*"([^"]+)"', r'"dateModified"\s*:\s*"([^"]+)"',
                r'property="article:published_time"\s+content="([^"]+)"', r'property="article:modified_time"\s+content="([^"]+)"',
                r'<time[^>]*datetime="([^"]+)"'):
        found += re.findall(pat, s)[:3]
    return list(dict.fromkeys(found))[:8]


def main():
    a = sys.argv[1:]
    url = a[0]
    grep = a[a.index("--grep") + 1] if "--grep" in a else None
    mx = int(a[a.index("--max") + 1]) if "--max" in a else 6000
    p = subprocess.run(["curl", "-sS", "-L", "--compressed", "--max-time", "45", "-A", UA, "-w", "\n%{http_code} %{url_effective}", url],
                       capture_output=True)
    out = p.stdout.decode("utf-8", "ignore")
    body, _, tail = out.rpartition("\n")
    code, _, final = tail.partition(" ")
    if p.returncode:
        print("FETCH FAILED:", p.stderr.decode("utf-8", "ignore").strip()[:300]); return
    t = text_of(body)
    title = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
    print("URL:", final); print("HTTP:", code); print("TITLE:", html.unescape(title.group(1)).strip() if title else "")
    print("DATES:", dates(body)); print("TEXT_CHARS:", len(t)); print("-----")
    src = body if "--raw" in a else t
    if grep:
        n = 0
        for m in re.finditer(grep, src, flags=re.I):
            print("…" + src[max(0, m.start() - 300):m.end() + 400].replace("\n", " ") + "…\n"); n += 1
            if n >= 8: break
        if not n: print("(no match for " + grep + ")")
    else:
        print(t[:mx])


main()
