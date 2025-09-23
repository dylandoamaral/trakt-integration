import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `custom_components` is importable
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]  # scripts -> trakt_tv -> custom_components -> repo root
sys.path.insert(0, str(REPO_ROOT))

from custom_components.trakt_tv.schema_meta import build_translations_en


def main():
    out = REPO_ROOT / "custom_components" / "trakt_tv" / "translations" / "en.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build_translations_en()
    out.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
