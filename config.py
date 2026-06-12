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

# --- Extraction (03) -----------------------------------------------------
EXTRACT_AUDIT_CLAUSES_N = 150   # precision audit sample
EXTRACT_AUDIT_NOGLOSS_N = 100   # recall audit sample
EXTRACT_AUDIT_LABEL_N = 25      # LABEL top-up audit sample (A1 only)
WATERMARK_V2_MIN_FORMATS = 300  # broadened watermark scan threshold

# --- Analysis (04) -------------------------------------------------------
PER_FORMAT_INSTANCE_CAP = 100   # seeded instance cap per format
N_PERMUTATIONS = 10000          # label permutations for headline test
BOOTSTRAP_N = 1000              # bootstrap resamples for shallow-cue CIs
FAMILY_CONTRAST_MIN_CLAUSES = 100  # per-family contrasts only at >= this; below: descriptive

# --- Block A (04B) -------------------------------------------------------
TAG_DIAG_TOP_PAIRS = 50         # highest-Jaccard pairs listed in the diagnostic
TAG_DIAG_MID_SAMPLE = 25        # seeded mid-range (0.1-0.3) pair sample

# --- Block B (04C): content layer ----------------------------------------
CONTENT_MODEL = "BAAI/bge-large-en-v1.5"  # symmetric mode, no query prefix
CONTENT_DECILES = 10
COMPLEMENT_MIN_FORMATS_PER_HEAD = 5
# Ratified light-head stoplist: clauses with these (or missing) complement
# heads drop out of the complement test only.
COMPLEMENT_HEAD_STOPLIST = (
    "feeling", "feelings", "sense", "emotion", "emotions", "way", "manner",
    "variety", "kind", "type", "sort", "form", "thing", "something")

# --- Block C (04D): visual layer ------------------------------------------
# Base (non-fine-tuned) SigLIP vectors from the SemioMeme release.
VISION_EMBEDDINGS_DIR = SEMIOMEME_ROOT / "data" / "retrieval_data" / "vision_embeddings"
VISION_METADATA_DIR = SEMIOMEME_ROOT / "data" / "retrieval_data" / "vision_metadata"
COHERENCE_SPLIT = "median"      # high-coherence = above population median
MIN_PAIRS_FLAG = 100            # flag cells below this many within-pairs

# --- Denoising (04F) -------------------------------------------------------
DENOISE_K = 5                   # nearest neighbours for typicality
DENOISE_PCTL_PRIMARY = 10       # global removal percentile (primary)
DENOISE_PCTL_SENS = 20          # sensitivity threshold
DENOISE_MIN_GALLERY = 7         # formats below this sample size are exempt
VISION_FT_CHECKPOINT = SEMIOMEME_ROOT / "data" / "corpus_data" / "vision_model.pth"

# --- Exhibits (05B) --------------------------------------------------------
EXHIBIT_SHORTLIST_N = 8         # 4 centroid-closest + 4 seeded-random
EXHIBIT_TEXTS_PER_FORMAT = 10   # seeded fill texts per shortlisted format
# Coarse-by-design flag pass; final selection happens in chat.
EXHIBIT_SLUR_LIST = "better_profanity 0.7.0 (LDNOOBW-derived wordlist)"

# --- Expected names: verify against the real files at runtime -----------
EXPECTED_ENTRY_TEXT_COL = "About Text"
EXPECTED_OCR_TEXT_COL = "Text"
EXPECTED_OCR_REF_COLS = ("Image Ref", "file")

if __name__ == "__main__":
    for name, p in [("ENTRIES_CSV", ENTRIES_CSV), ("OCR_CONFIRMED_CSV", OCR_CONFIRMED_CSV)]:
        status = "OK" if p.exists() else "MISSING"
        print(f"{status}: {name} -> {p}")
