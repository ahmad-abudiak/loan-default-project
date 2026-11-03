"""Model pipelines for the loan default project."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, QuantileTransformer

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