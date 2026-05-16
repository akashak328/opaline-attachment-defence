"""
feature_extraction.py
─────────────────────
Extracts features from the preprocessed email dataset using:
  - Bag of Words (CountVectorizer)
  - TF-IDF (TfidfVectorizer)
  - Word frequency analysis & visualizations
"""

import re
import string
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import LabelEncoder

from gensim.parsing.preprocessing import STOPWORDS

warnings.filterwarnings("ignore")
stop_words = set(STOPWORDS)


def load_emails(csv_path: str = "static/dataset/spam.csv") -> pd.DataFrame:
    emails = pd.read_csv(csv_path, encoding="ISO-8859-1")
    emails = emails.rename(columns={"v1": "Classify", "v2": "Email"})
    emails.drop_duplicates(inplace=True)
    emails.dropna(subset=["Email"], inplace=True)
    return emails


def clean_emails(emails: pd.DataFrame) -> pd.DataFrame:
    # Remove punctuation
    emails['Email'] = emails['Email'].apply(
        lambda x: x.translate(str.maketrans('', '', string.punctuation))
    )
    # Lowercase
    emails['Email'] = emails['Email'].str.lower()
    # Remove stopwords
    emails['Email'] = emails['Email'].apply(
        lambda x: ' '.join([w for w in x.split() if w not in stop_words])
    )
    return emails


def plot_character_distribution(emails: pd.DataFrame, save_path: str = "static/graph/ff2.png"):
    emails['num_chars'] = emails['Email'].apply(len)
    emails['num_chars'].hist(bins=50)
    plt.xlabel('Number of characters in the message')
    plt.ylabel('Frequency')
    plt.title('Distribution of number of characters in messages')
    plt.savefig(save_path)
    plt.close()
    print(f"[INFO] Character distribution chart saved → {save_path}")


def generate_wordcloud(emails: pd.DataFrame, save_path: str = "static/graph/wordcloud.png"):
    all_words   = ' '.join(emails['Email']).split()
    word_counts = Counter(all_words)
    most_common = word_counts.most_common(100)
    wc = WordCloud(width=800, height=400, background_color='white')
    wc.generate_from_frequencies(dict(most_common))
    plt.figure(figsize=(10, 6))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(save_path)
    plt.close()
    print(f"[INFO] Word cloud saved → {save_path}")


def extract_bow(emails: pd.DataFrame):
    """Bag-of-Words feature matrix."""
    vectorizer = CountVectorizer()
    bow        = vectorizer.fit_transform(emails['Email'])
    print(f"[INFO] BoW matrix shape: {bow.shape}")
    return vectorizer, bow


def extract_tfidf(emails: pd.DataFrame):
    """TF-IDF feature matrix."""
    tfidf_vec = TfidfVectorizer(max_features=5000)
    tfidf_mat = tfidf_vec.fit_transform(emails['Email'])
    print(f"[INFO] TF-IDF matrix shape: {tfidf_mat.shape}")
    return tfidf_vec, tfidf_mat


def encode_labels(emails: pd.DataFrame):
    """Encode Classify column: ham=0, spam=1."""
    le     = LabelEncoder()
    labels = le.fit_transform(emails['Classify'])
    return labels, le


def run_feature_extraction(csv_path: str = "static/dataset/spam.csv"):
    """Full pipeline: load → clean → plot → extract features."""
    print("[INFO] Loading dataset...")
    emails = load_emails(csv_path)
    print(f"[INFO] Dataset shape: {emails.shape}")
    print(f"[INFO] Spam: {(emails['Classify']=='spam').sum()}  |  Ham: {(emails['Classify']=='ham').sum()}")

    print("[INFO] Cleaning emails...")
    emails = clean_emails(emails)

    plot_character_distribution(emails)
    generate_wordcloud(emails)

    vectorizer, bow   = extract_bow(emails)
    tfidf_vec, tfidf  = extract_tfidf(emails)
    labels, le        = encode_labels(emails)

    return {
        "emails":      emails,
        "bow":         bow,
        "tfidf":       tfidf,
        "vectorizer":  vectorizer,
        "tfidf_vec":   tfidf_vec,
        "labels":      labels,
        "label_enc":   le,
    }


if __name__ == "__main__":
    results = run_feature_extraction()
    print("[DONE] Feature extraction complete.")
