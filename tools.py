"""Data access tools used by the agent: product catalog and orders."""

import unicodedata
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
CSV_PREFIX = "desafio_tecnico_ai_eng - "  # original file names are kept unchanged


def read_table(name: str) -> pd.DataFrame:
    """Read one of the provided CSV files by table name, e.g. "products"."""
    path = DATA_DIR / f"{CSV_PREFIX}{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}. Keep the original file names in data/.")
    return pd.read_csv(path)


def normalize_text(text: str) -> str:
    """Lowercase text and remove accents, so "Violão" and "violao" match."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_accents.casefold().strip()