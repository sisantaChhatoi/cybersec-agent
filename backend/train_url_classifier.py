"""Train a URL phishing/malware classifier and save to data/url_classifier.joblib."""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("D:/Downloads/malicious_phish.csv/malicious_phish.csv")
OUT_PATH = Path(__file__).parent / "data" / "url_classifier.joblib"

_SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".tk", ".buzz", ".click", ".ml", ".ga", ".cf",
    ".gq", ".pw", ".icu", ".live", ".online", ".work", ".loan", ".win",
    ".bid", ".trade", ".racing", ".date", ".download", ".info",
}
_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "buff.ly",
    "tiny.cc", "is.gd", "rb.gy", "cutt.ly",
}
_SCAM_KEYWORDS = {
    "login", "verify", "kyc", "otp", "refund", "prize", "reward",
    "secure", "update", "confirm", "account", "bank", "wallet",
    "winner", "claim", "gift", "lucky", "urgent", "alert", "suspend",
    "blocked", "freeze", "recover", "redeem",
}


def extract_features(url: str) -> list[float]:
    try:
        if not url.startswith("http"):
            url = "http://" + url
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = (parsed.path or "").lower()
        parts = host.split(".")
        domain_label = parts[-2] if len(parts) >= 2 else host
        tld = f".{parts[-1]}" if parts else ""
        combined = host + path
    except Exception:
        return [0.0] * 12

    return [
        float(len(url)),
        float(host.count(".")),
        float(domain_label.count("-")),
        float(sum(c.isdigit() for c in domain_label)),
        float(tld in _SUSPICIOUS_TLDS),
        float(any(p.startswith("xn--") for p in parts)),
        float("@" in url),
        float(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host))),
        float(host.removeprefix("www.") in _SHORTENERS),
        float(any(kw in combined for kw in _SCAM_KEYWORDS)),
        float(len(parts) > 3),
        float(len(path)),
    ]


def main() -> None:
    print(f"Loading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH)
    print(f"Rows: {len(df)}  Classes: {df['type'].value_counts().to_dict()}")

    print("Extracting features ...")
    X = np.array([extract_features(u) for u in df["url"]], dtype=np.float32)
    le = LabelEncoder()
    y = le.fit_transform(df["type"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train: {len(X_train)}  Test: {len(X_test)}")

    print("Training logistic regression ...")
    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(max_iter=2000, C=1.0, n_jobs=-1, class_weight="balanced", solver="saga")),
    ])
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "label_encoder": le}, OUT_PATH)
    print(f"Model saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
