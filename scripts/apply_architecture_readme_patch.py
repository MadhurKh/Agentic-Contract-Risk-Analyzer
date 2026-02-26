from __future__ import annotations
from pathlib import Path

ARCH_SECTION = """## 🗺️ Architecture Diagram

![Architecture Diagram](docs/assets/architecture.png)

More detail: `docs/architecture.md`

---
"""

def patch_readme(readme_path: Path) -> bool:
    if not readme_path.exists():
        return False
    txt = readme_path.read_text(encoding="utf-8", errors="ignore")
    if "## 🗺️ Architecture Diagram" in txt:
        return True

    marker = "## 🧠 Architecture Overview (5-Agent System)"
    if marker in txt:
        before, after = txt.split(marker, 1)
        txt2 = before + ARCH_SECTION + "\n" + marker + after
    else:
        # Append near top (after first horizontal rule if present)
        hr = "\n---\n"
        if hr in txt:
            a, b = txt.split(hr, 1)
            txt2 = a + hr + "\n" + ARCH_SECTION + b
        else:
            txt2 = txt + "\n\n" + ARCH_SECTION

    readme_path.write_text(txt2, encoding="utf-8")
    return True

def patch_hiring_manager_readme(hm_path: Path) -> bool:
    if not hm_path.exists():
        return False
    txt = hm_path.read_text(encoding="utf-8", errors="ignore")
    if "Architecture Diagram" in txt:
        return True
    add = "\n\n## Architecture Diagram\n\nSee: `docs/architecture.md` (includes a visual diagram of the multi-agent pipeline and the local-PDF-only grounding constraint).\n"
    hm_path.write_text(txt + add, encoding="utf-8")
    return True

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    patched_any = False

    # Root README
    patched_any |= patch_readme(root / "README.md")

    # Hiring manager readme: try common locations
    patched_any |= patch_hiring_manager_readme(root / "README_FOR_HIRING_MANAGER.md")
    patched_any |= patch_hiring_manager_readme(root / "docs" / "hiring_manager_pack" / "README_FOR_HIRING_MANAGER.md")

    return 0 if patched_any else 1

if __name__ == "__main__":
    raise SystemExit(main())
