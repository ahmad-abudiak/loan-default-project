"""Drift monitoring: Population Stability Index (PSI)."""

import numpy as np
import pandas as pd


def psi_numeric(expected, actual, bins=10):
    """PSI for a numeric feature, using bins cut from the expected (training) data."""
    expected = pd.Series(expected, dtype="float64").reset_index(drop=True)
    actual = pd.Series(actual, dtype="float64").reset_index(drop=True)

    cuts = np.unique(np.nanquantile(expected, np.linspace(0, 1, bins + 1)))
    edges = np.concatenate([[-np.inf], cuts[1:-1], [np.inf]])

    def shares(values):
        counts = pd.cut(values, edges).value_counts(sort=False).values
        missing = values.isna().sum()
        return np.append(counts, missing) / len(values)

    return _psi_from_shares(shares(expected), shares(actual))


def psi_categorical(expected, actual):
    """PSI for a categorical feature: compares the share of each category."""
    expected = pd.Series(expected).astype("object").fillna("Missing").astype(str)
    actual = pd.Series(actual).astype("object").fillna("Missing").astype(str)
    categories = sorted(set(expected) | set(actual))
    e = expected.value_counts(normalize=True).reindex(categories, fill_value=0).values
    a = actual.value_counts(normalize=True).reindex(categories, fill_value=0).values
    return _psi_from_shares(e, a)


def _psi_from_shares(expected_shares, actual_shares, eps=1e-4):
    e = np.clip(expected_shares, eps, None)
    a = np.clip(actual_shares, eps, None)
    return float(np.sum((a - e) * np.log(a / e)))


def psi_label(value):
    """Translate a PSI value into the usual rule of thumb."""
    if value < 0.1:
        return "Stable"
    if value < 0.25:
        return "Watch"
    return "Act"