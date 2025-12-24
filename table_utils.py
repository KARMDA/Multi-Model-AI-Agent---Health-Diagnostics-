"""
table_utils.py
Creates pivot views and summary tables for interpreted parameter rows.
"""

import pandas as pd


def pivot_params_to_wide(df):
    df = df.copy()
    df["param_col"] = df.apply(
        lambda r: f"{r['canonical']} ({r['unit_std']})" if r["unit_std"] else r["canonical"],
        axis=1
    )
    return df.pivot_table(
        index=["patient_id", "filename", "age", "gender"],
        columns="param_col",
        values="value_std",
        aggfunc="first"
    ).reset_index()


def summary_counts_by_interpretation(df):
    return df.groupby(["canonical", "interpretation"]).size().unstack(fill_value=0)


def patient_level_flag(df):
    df = df.copy()
    df["abn"] = df["interpretation"].isin(["low", "high", "borderline_low", "borderline_high"])
    out = df.groupby("patient_id").agg(
        n_params=("canonical", "count"),
        n_abnormal=("abn", "sum")
    )
    out["any_abnormal"] = out["n_abnormal"] > 0
    return out.reset_index()

















