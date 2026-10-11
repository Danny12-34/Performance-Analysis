import re
import pdfplumber
import pandas as pd

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------
# Lines containing any of these words are headers/footers, not students
SKIP_PATTERN = re.compile(
    r"\b(?:academic year|total|average|page|class|subject|teacher|"
    r"reg number|student name|marks|printed|signature|highest|lowest)\b",
    re.IGNORECASE,
)

# Words used in marksheets when a student did not sit the exam
ABSENT_WORDS = {"AB", "ABS", "ABSENT", "-", "--", "N/A", "NA", "X"}

# reg number (optional) + name (letters, spaces, . ' -) + mark (number or absent word)
LINE_PATTERN = re.compile(
    r"^(?:(?P<reg>\d[\d/\-]*)\s+)?"
    r"(?P<name>[^\d\n]+?)\s+"
    r"(?P<mark>\d+(?:[.,]\d+)?|AB|ABS|ABSENT|N/A|NA|X|--|-)$",
    re.IGNORECASE,
)


def _clean_name(name: str) -> str:
    """Collapse extra spaces and strip stray punctuation around the name."""
    name = re.sub(r"\s+", " ", name).strip(" .:;,-_|")
    return name


def _parse_mark(raw: str, absent_as: float):
    """Convert the mark text to a float. Returns None if it cannot be parsed."""
    raw = raw.strip().upper()
    if raw in ABSENT_WORDS:
        return absent_as
    try:
        mark = float(raw.replace(",", "."))
    except ValueError:
        return None
    # Some systems store a real zero as 0.01
    if mark == 0.01:
        mark = 0.0
    return mark


def extract_marks(pdf_file, absent_as: float = 0.0, max_mark: float | None = None) -> pd.DataFrame:
    """
    Extract student marks from a PDF marksheet.

    Parameters
    ----------
    pdf_file  : path or file-like object (works with Streamlit's uploaded files)
    absent_as : value to use when a student is marked absent (AB, ABS, -, ...)
    max_mark  : optional. If given, marks above this value are ignored (likely
                to be totals or page numbers rather than student marks)

    Returns
    -------
    DataFrame with columns: "Reg Number", "Student Name", "Marks"
    """
    # Streamlit file objects may already have been read once
    if hasattr(pdf_file, "seek"):
        try:
            pdf_file.seek(0)
        except Exception:
            pass

    rows = []

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                for line in text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    if SKIP_PATTERN.search(line):
                        continue

                    match = LINE_PATTERN.match(line)
                    if not match:
                        continue

                    name = _clean_name(match.group("name"))
                    # Need at least 2 letters to be a real name
                    if len(re.sub(r"[^A-Za-z]", "", name)) < 2:
                        continue

                    mark = _parse_mark(match.group("mark"), absent_as)
                    if mark is None or mark < 0:
                        continue
                    if max_mark is not None and mark > max_mark:
                        continue

                    reg = match.group("reg") or "N/A"
                    rows.append([reg, name, mark])
    except Exception as e:
        raise ValueError(f"Could not read the PDF file: {e}") from e

    df = pd.DataFrame(rows, columns=["Reg Number", "Student Name", "Marks"])

    if df.empty:
        raise ValueError(
            "No student marks were found in this PDF. "
            "Make sure it is a text-based PDF (not a scanned image) with lines like "
            "'<reg number> <student name> <mark>'."
        )

    # Remove accidental duplicates (same reg number repeated, e.g. a header row repeated on every page)
    has_reg = df["Reg Number"] != "N/A"
    df = pd.concat([
        df[has_reg].drop_duplicates(subset=["Reg Number", "Student Name"], keep="first"),
        df[~has_reg],
    ]).sort_index().reset_index(drop=True)

    return df