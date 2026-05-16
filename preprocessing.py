"""
preprocessing.py
────────────────
NLP preprocessing pipeline for email text:
tokenization → cleaning → stopword removal → stemming → lemmatization
"""

import re
import string
import warnings
import pandas as pd
from collections import Counter

from gensim.parsing.preprocessing import STOPWORDS
from gensim.parsing.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer

warnings.filterwarnings("ignore")

stemmer    = PorterStemmer()
lematizer  = WordNetLemmatizer()
stop_words = set(STOPWORDS)


# ── Text Cleaning Helpers ──────────────────────────────────────────────────────

def lower(text: str) -> str:
    return text.lower()


def remove_specChar(text: str) -> str:
    return re.sub("#[A-Za-z0-9_]+", ' ', text)


def remove_link(text: str) -> str:
    return re.sub(r'@\S+|https?:\S+|http?:\S|[^A-Za-z0-9]+', ' ', text)


def remove_stopwords(text: str) -> str:
    return " ".join([word for word in str(text).split() if word not in STOPWORDS])


def stemming(text: str) -> str:
    return " ".join([stemmer.stem(word) for word in text.split()])


def stem_s(word: str) -> str:
    """Remove trailing 's' from words (simple plural reduction)."""
    ww  = word.split(" ")
    wd  = []
    for wr in ww:
        w1  = len(wr) - 1
        w2  = len(wr)
        wrr = wr[w1:w2]
        wd.append(wr[:-1] if wrr == 's' else wr)
    return " ".join(wd)


def lemmatizer_words(text: str) -> str:
    return " ".join([lematizer.lemmatize(word) for word in text.split()])


def cleanTxt(text: str) -> str:
    """Full cleaning pipeline."""
    text = lower(text)
    text = remove_specChar(text)
    text = remove_link(text)
    text = remove_stopwords(text)
    text = stemming(text)
    text = stem_s(text)
    return text


# ── Tokenizer ─────────────────────────────────────────────────────────────────

def generate_token(query: str) -> list:
    """Clean and tokenize a query string, removing stopwords."""
    q4     = []
    query1 = ""
    q1     = query.split(" ")
    for q11 in q1:
        q2 = q11.split(".")
        q3 = "".join(q2)
        q4.append(q3)
    query1 = " ".join(q4)
    text   = cleanTxt(query1)
    text_tokens        = text.split(" ")
    tokens_without_sw  = [word for word in text_tokens if word not in stop_words]
    return tokens_without_sw


# ── Dataset Loaders ────────────────────────────────────────────────────────────

def load_data(csv_path: str = "static/dataset/spam.csv", limit: int = 200) -> list:
    """Load raw email dataset and return first `limit` rows."""
    pd.set_option("display.max_colwidth", 200)
    data = pd.read_csv(
        csv_path,
        header=0,
        encoding="latin-1",
        usecols=[0, 1],
        names=["label", "text"],
    )
    data1 = []
    for i, ds in enumerate(data.values):
        if i >= limit:
            break
        data1.append(ds)
    return data1


def preprocess(csv_path: str = "static/dataset/spam.csv", limit: int = 200):
    """
    Preprocess dataset: returns two lists —
      data1 → [original_text, token_list]
      data2 → [original_text, cleaned_text]
    """
    df = pd.read_csv(
        csv_path,
        header=0,
        encoding="latin-1",
        usecols=[0, 1],
        names=["label", "text"],
    )

    data1, data2 = [], []

    for i, ds in enumerate(df.values):
        if i >= limit:
            break
        if ds[1] == "":
            continue

        # Token list
        dt1 = [ds[1], generate_token(ds[1])]
        data1.append(dt1)

        # Cleaned text
        dt2 = [ds[1], cleanTxt(ds[1])]
        data2.append(dt2)

    return data1, data2
