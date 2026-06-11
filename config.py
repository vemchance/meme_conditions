"""Project configuration. Paths wired to the local SemioMeme tree."""
from pathlib import Path

# --- Local data locations ----------------------------------------------
# Derived from the SemioMeme project config (PROJECT_ROOT = X:\PhD\SemioMeme_Graph):
#   Meta.INPUT_FILE      -> data/meta_data/cleaned_data/cleaned_source_data.csv
#   Retrieval.OCR_FILES  -> data/corpus_data/ocr/confirmed_memes_full.csv
SEMIOMEME_ROOT = Path(r"X:\PhD\SemioMeme_Graph")
ENTRIES_CSV = SEMIOMEME_ROOT / "data" / "meta_data" / "cleaned_data" / "cleaned_source_data.csv"
OCR_CONFIRMED_CSV = SEMIOMEME_ROOT / "data" / "corpus_data" / "ocr" / "confirmed_memes_full.csv"

# Zenodo-release layout, for reproduction from the public dataset:
#   ENTRIES_CSV       = <release>/source_data/KYM_metadata/cleaned_source_data.csv
#   OCR_CONFIRMED_CSV = <release>/source_data/OCR_text/confirmed_memes_full.csv

# --- Repo-local ---------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
SAMPLES_DIR = OUTPUTS_DIR / "samples"

# --- Gate parameters ----------------------------------------------------
RANDOM_SEED = 1706      # deadline day
MIN_TOKENS = 3          # usable OCR text threshold (whitespace tokens)
MIN_INSTANCES = 20      # usable instances per format
SAMPLE_N = 500          # Gate C sample size

# --- Expected names: verify against the real files at runtime -----------
EXPECTED_ENTRY_TEXT_COL = "About Text"
EXPECTED_OCR_TEXT_COL = "Text"
EXPECTED_OCR_REF_COLS = ("Image Ref", "file")

if __name__ == "__main__":
    for name, p in [("ENTRIES_CSV", ENTRIES_CSV), ("OCR_CONFIRMED_CSV", OCR_CONFIRMED_CSV)]:
        status = "OK" if p.exists() else "MISSING"
        print(f"{status}: {name} -> {p}")
