"""Internal render worker; the public CLI bounds this process externally."""
import argparse
import json
import sys

from .views import render_case


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--revision", type=int)
    args = parser.parse_args()
    try:
        result = render_case(args.case_dir, args.output_dir, args.revision)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"format": "genius-consumer-error/0.1.0", "error": type(exc).__name__,
                          "reason": str(exc), "publication_state": "NOT_PUBLISHED",
                          "mathematical_conclusion": "NOT_EVALUATED"}, ensure_ascii=True, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
