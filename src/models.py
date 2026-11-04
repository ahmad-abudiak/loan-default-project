"""Model pipelines for the loan default project."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, QuantileTransformer
from lightgbm import LGBMClassifier
from sklearn.preprocessing import OrdinalEncoder
import numpy as np

from src.features import build_features


def build_logistic_pipeline(numeric_features, categorical_features, binary_features):
    """Feature engineering + preprocessing + logistic regression in one pipeline."""
    numeric_steps = Pipeline([
        ("quantile", QuantileTransformer(
            output_distribution="normal",
            n_quantiles=1000,
            subsample=200_000,
            random_state=42,
        )),
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
    ])

    preprocess = ColumnTransformer([
        ("num", numeric_steps, numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("bin", "passthrough", binary_features),
    ])

    return Pipeline([
        ("features", FunctionTransformer(build_features)),
        ("preprocess", preprocess),
        ("model", LogisticRegression(max_iter=1000)),
    ])


def build_lightgbm_preprocessor(numeric_features, categorical_features, binary_features):
    """Feature engineering + light preprocessing for LightGBM."""
    preprocess = ColumnTransformer(
        [
            ("num", "passthrough", numeric_features),
            ("cat", OrdinalEncoder(
                handle_unknown="use_encoded_value",
                unknown_value=-1,
                encoded_missing_value=-1,
            ), categorical_features),
            ("bin", "passthrough", binary_features),
        ],
        verbose_feature_names_out=False,
    )
    preprocess.set_output(transform="pandas")

    return Pipeline([
        ("features", FunctionTransformer(build_features)),
        ("preprocess", preprocess),
    ])


def build_lightgbm_model(**params):
    """LightGBM classifier with sensible defaults; any setting can be overridden."""
    settings = {
        "n_estimators": 5000,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 200,
        "subsample": 0.8,
        "subsample_freq": 1,
        "colsample_bytree": 0.8,
        "reg_lambda": 1.0,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1,
    }
    settings.update(params)
    return LGBMClassifier(**settings)



def logit(p):
    """Convert probabilities to log-odds (the scale logistic regression works on)."""
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


class CalibratedModel:
    """A trained pipeline plus a probability correction (Platt scaling)."""

    def __init__(self, pipeline, calibrator):
        self.pipeline = pipeline
        self.calibrator = calibrator

    def predict_proba(self, X):
        raw = self.pipeline.predict_proba(X)[:, 1]
        corrected = self.calibrator.predict_proba(logit(raw).reshape(-1, 1))[:, 1]
        return np.column_stack([1 - corrected, corrected])