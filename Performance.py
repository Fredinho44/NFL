# pages/performance.py
import streamlit as st
import pandas as pd
import os

def load_results(file_path):
    """Load results CSV with UTF-8 first, then Latin-1 fallback."""
    try:
        return pd.read_csv(file_path), False
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="latin1"), True

def run():
    st.header("📊 Model Performance Dashboard")

    file_path = "C:\\Users\\User\\Desktop\\NFL_Model\\data\\predictions_with_results_1.csv"

    if not os.path.exists(file_path):
        st.error("predictions_with_results.csv not found.")
        return

    df, used_fallback = load_results(file_path)
    if used_fallback:
        st.info("Loaded results with Latin-1 encoding due to non-UTF8 characters.")

    # Week selector
    if "week" in df.columns:
        df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")
        weeks = sorted(df["week"].dropna().unique())
        if weeks:
            default_idx = len(weeks) - 1  # latest week by default
            selected_week = st.selectbox("Week", weeks, index=default_idx)
            df = df[df["week"] == selected_week]
            st.write(f"Showing {len(df)} games for week {selected_week}.")
        else:
            st.warning("No week values found in results.")

    # Key metrics
    if "spread_pick_hit" in df:
        spread_acc = df["spread_pick_hit"].mean() * 100
        st.metric("Spread Accuracy", f"{spread_acc:.2f}%")

    if "total_pick_hit" in df:
        total_acc = df["total_pick_hit"].mean() * 100
        st.metric("Total Accuracy", f"{total_acc:.2f}%")

    if "model_beats_vegas_spread" in df:
        st.metric("Model Beats Vegas (Spread)", f"{df.model_beats_vegas_spread.mean() * 100:.2f}%")

    if "model_beats_vegas_total" in df:
        st.metric("Model Beats Vegas (Total)", f"{df.model_beats_vegas_total.mean() * 100:.2f}%")

    st.subheader("Spread Error Distribution")
    if "model_spread_error" in df:
        st.bar_chart(df["model_spread_error"])

    st.subheader("Total Error Distribution")
    if "model_total_error" in df:
        st.bar_chart(df["model_total_error"])

    st.subheader("Full Results")
    st.dataframe(df)
