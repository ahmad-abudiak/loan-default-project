"""SHAP explanations for individual applicants."""

import pandas as pd
import shap


def make_explainer(calibrated_model):
    """Create a SHAP explainer for the LightGBM model inside the calibrated model."""
    return shap.TreeExplainer(calibrated_model.pipeline.named_steps["model"])


def explain_applicant(calibrated_model, explainer, applicant, top_n=5):
    """Return the features that pushed this applicant's risk up or down the most."""
    prep = calibrated_model.pipeline.named_steps["prep"]

    readable = prep.named_steps["features"].transform(applicant)
    model_input = prep.transform(applicant)

    values = explainer.shap_values(model_input)
    if isinstance(values, list):
        values = values[1]
    if values.ndim == 3:
        values = values[:, :, 1]

    result = pd.DataFrame({
        "feature": model_input.columns,
        "value": [readable[c].iloc[0] for c in model_input.columns],
        "contribution": values[0],
    })
    result["effect"] = result["contribution"].apply(
        lambda c: "raises risk" if c > 0 else "lowers risk"
    )
    result["size"] = result["contribution"].abs()
    return (
        result.sort_values("size", ascending=False)
        .head(top_n)
        .drop(columns="size")
        .reset_index(drop=True)
    )