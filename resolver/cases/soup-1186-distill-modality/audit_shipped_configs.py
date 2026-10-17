"""Read-only audit of shipped YAML and recipe literals; no Soup imports."""
import ast
import json
from pathlib import Path
import sys

import yaml

root = Path(sys.argv[1]).resolve()
captures = []
for dirname in ("templates", "examples", "src/soup_cli/templates"):
    for path in sorted((root / dirname).rglob("*")):
        if path.suffix in (".yaml", ".yml"):
            captures.append((str(path.relative_to(root)), yaml.safe_load(path.read_text())))
catalog = root / "src/soup_cli/recipes/catalog.py"
tree = ast.parse(catalog.read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "RecipeMeta":
            fields = {field.arg: field.value for field in node.keywords}
            raw = ast.literal_eval(fields["yaml_str"])
            captures.append((f"recipes/catalog.py:{node.lineno}", yaml.safe_load(raw)))

distill = []
for name, config in captures:
    if isinstance(config, dict) and config.get("task") == "distill":
        distill.append({"source": name, "modality": config.get("modality", "text")})
offenders = [entry for entry in distill if entry["modality"] != "text"]
assert len(captures) > 100, "Unexpectedly empty shipped-config inventory"
print(json.dumps({"inspected": len(captures), "sources": [n for n, _ in captures],
                  "distillation_configs": distill, "non_text_distillation": offenders}, indent=2))
raise SystemExit(bool(offenders))
