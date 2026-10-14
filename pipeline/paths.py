"""Where everything lives. The layout follows cldfbench (https://github.com/cldf/cldfbench):

  raw/    source data, never changed: the course documents, the owner's spreadsheet and notes
  etc/    curation: lesson classification, translations, verb details, corrections, decisions
  cldf/   the CLDF dataset, regenerated from raw/ + etc/ by `cldfbench makecldf` on every build
"""
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent
ROOT = PIPELINE.parent                       # the repository root (the cldfbench dataset)
RAW = ROOT / "raw"
ETC = ROOT / "etc"
CLDF = ROOT / "cldf"
CACHE = PIPELINE / "cache"
DATA = PIPELINE / "data"
TEMPLATES = PIPELINE / "templates"
# raw/ is a git submodule of this GitHub repo (private for now): the pages link to the documents there,
# since GitHub does not follow relative links into a submodule
RAW_URL = "https://github.com/michaelmaguire/languages-dialett-raw"


def raw_available():
    """True when the source documents are present. raw/ is a git submodule
    (michaelmaguire/languages-dialett-raw) that may be private: without it, steps 1-2 cannot run and
    the build starts from what they last saved in pipeline/data/ (see pipeline/README.md)."""
    return RAW.is_dir() and any(p.suffix.lower() in (".docx", ".pdf") for p in RAW.iterdir())
