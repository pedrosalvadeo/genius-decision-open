"""Download public pages and check that quoted phrases appear in them, verbatim.

Any domain: a twin's claims quote their sources, and this node confirms each quote
against the live page from an open network (GitHub runners), recording the page's
SHA-256 and the sentence around each phrase. It contacts no one; it only reads.

Run (needs network):
  python twin/history/source_quotes.py twin/history/blood_2026/quotes.json --out out/blood_quotes.json
The input is [{"url", "phrases": [...]}]. Matching ignores case and collapses whitespace.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.request

AGENT = 'Mozilla/5.0 (compatible; genius-history-node)'


def text_of(raw):
    page = raw.decode('utf-8', 'replace')
    page = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', page)
    page = re.sub(r'(?s)<[^>]+>', ' ', page)
    return re.sub(r'\s+', ' ', html.unescape(page)).strip()


def check(entry):
    out = dict(url=entry['url'], phrases=[])
    try:
        request = urllib.request.Request(entry['url'], headers={'User-Agent': AGENT, 'Accept-Language': 'en,es'})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
        out.update(status=response.status, sha256=hashlib.sha256(raw).hexdigest())
    except Exception as exc:  # report and move on: one dead page does not stop the node
        out.update(error=str(exc))
        return out
    text = text_of(raw)
    lowered = text.lower()
    for phrase in entry['phrases']:
        at = lowered.find(re.sub(r'\s+', ' ', phrase).lower())
        out['phrases'].append(dict(phrase=phrase, found=at >= 0, context=text[max(0, at - 300):at + len(phrase) + 300] if at >= 0 else None))
    out['found_numbers'] = sorted(set(re.findall(r'[^.]{0,120}\b\d[\d,.]*\s*(?:%|days?|day|units?|unidades|donantes|donations?|percent)[^.]{0,120}', text)))[:40]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('quotes')
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    results = [check(entry) for entry in json.loads(Path(args.quotes).read_text())]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(results, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
