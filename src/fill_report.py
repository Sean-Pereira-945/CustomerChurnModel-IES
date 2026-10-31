"""Fill {{B.*}} and {{C.*}} placeholders in the management report from the JSON outputs.

Placeholder syntax:  {{B.key}}  {{C.key}}  {{B.key|fmt}}  {{B.nested.key|fmt}}
  B.* -> out/B/metrics.json      C.* -> out/C/eda_findings.json
Formats: pct, pct1, f2, f3, aed_m, aed, int, x2  (default: str)
A missing key raises KeyError (fail loudly, never leave a gap).

Run: python fill_report.py            # uses default paths
"""
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{([BC])\.([^|}]+?)(?:\|(\w+))?\}\}")


def resolve_base(arg=None):
    """Find the out/ folder (holding A/ B/ C/) whether run from src/ or from out/C."""
    here = Path(__file__).resolve().parent
    candidates = [arg] if arg else []
    candidates += [Path.cwd() / "out", Path.cwd() / "../out", here / "../out",
                   here.parent, here.parent.parent / "out", here.parent / "out"]
    for c in candidates:
        if c and (Path(c) / "B" / "metrics.json").exists():
            return Path(c)
    return Path(arg or "../out")


def flatten(d, prefix=""):
    flat = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            flat.update(flatten(v, key + "."))
        else:
            flat[key] = v
    return flat


def fmt(value, spec):
    if spec in (None, "str"):
        return f"{value:,}" if isinstance(value, int) else str(value)
    v = float(value)
    return {
        "pct": f"{v:.0%}", "pct1": f"{v:.1%}", "f2": f"{v:.2f}", "f3": f"{v:.3f}",
        "aed_m": f"{v/1e6:.1f}m", "aed": f"{v:,.0f}", "int": f"{int(round(v)):,}",
        "x2": f"{v:.2f}×",
    }[spec]


def build_lookup(metrics_path, eda_path):
    B = flatten(json.loads(Path(metrics_path).read_text(encoding="utf-8")))
    C = flatten(json.loads(Path(eda_path).read_text(encoding="utf-8")))
    return {"B": B, "C": C}


def fill_text(text, lookup):
    def repl(m):
        ns, key, spec = m.group(1), m.group(2).strip(), m.group(3)
        table = lookup[ns]
        if key not in table:
            raise KeyError(f"{ns}.{key} not found in {ns} JSON (placeholder cannot be filled)")
        return fmt(table[key], spec)
    return PLACEHOLDER.sub(repl, text)


def main(base=None):
    base = resolve_base(base)
    lookup = build_lookup(base / "B" / "metrics.json", base / "C" / "eda_findings.json")
    src = base / "C" / "management_report.md"
    text = fill_text(src.read_text(encoding="utf-8"), lookup)
    dst = base / "C" / "management_report_filled.md"
    dst.write_text(text, encoding="utf-8")
    words = len(re.findall(r"\b\w+\b", re.sub(r"[#*|`>-]", " ", text)))
    print(f"Filled report -> {dst}  (~{words} words)")
    remaining = PLACEHOLDER.findall(text)
    print("Unfilled placeholders:", len(remaining))
    return words


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
