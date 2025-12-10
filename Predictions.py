# pages/predictions.py
import os
import pandas as pd
import streamlit as st


def load_predictions(file_path: str):
    """Load predictions from JSON only. Returns (df, used_fallback, ext)."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext != ".json":
        raise ValueError("Expected a JSON predictions file.")
    return pd.read_json(file_path), False, ext


def run():
    st.header("NFL Game Predictions")

    json_path = "C:\\Users\\User\\Desktop\\NFL_Model\\data\\predictions_2023_2025.json"
    if not os.path.exists(json_path):
        st.error("Predictions JSON not found. Run the generator to create predictions_2023_2025.json.")
        return
    file_path = json_path

    df, used_fallback, ext = load_predictions(file_path)
    if used_fallback:
        st.info("Loaded predictions with Latin-1 encoding due to non-UTF8 characters.")
    st.caption(f"Loaded predictions from {os.path.basename(file_path)}")

    # Convert key numeric fields (JSON may store them as strings with +/-)
    numeric_cols = [
        "week", "spread_confidence", "spread_win_prob", "spread_std_game",
        "spread_variance", "suggested_units", "edge_vs_spread",
        "projected_spread_home_minus_away", "home_line", "away_line",
        "sportsbook_home_spread", "consensus_home_spread",
        "projected_first_half_spread_home_minus_away",
        "projected_total_points", "sportsbook_total", "edge_vs_total",
        "total_confidence",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derive helper columns
    if {"away_team", "home_team"}.issubset(df.columns):
        df["matchup"] = df["away_team"].fillna("") + " @ " + df["home_team"].fillna("")
    if "edge_vs_spread" in df.columns:
        df["bet_side"] = df["edge_vs_spread"].apply(lambda x: "Home" if pd.notna(x) and x >= 0 else "Away")
    # Predicted spread oriented to the model pick (home_line if picking home, else away_line)
    if {"home_line", "away_line", "model_pick", "home_team", "away_team"}.issubset(df.columns):
        df["predicted_spread"] = df.apply(
            lambda row: row["home_line"] if row["model_pick"] == row["home_team"] else row["away_line"],
            axis=1,
        )
    elif "projected_spread_home_minus_away" in df.columns:
        df["predicted_spread"] = df["projected_spread_home_minus_away"]
    # Format kickoff times (Eastern) for display
    if "kickoff_et" in df.columns:
        df["kickoff_local"] = pd.to_datetime(df["kickoff_et"], errors="coerce")
        df["kickoff_local"] = df["kickoff_local"].dt.strftime("%a %b %d, %I:%M %p").fillna(df["kickoff_et"])

    # Sort by strongest plays first if available
    sort_cols = [c for c in ["suggested_units", "spread_confidence", "edge_vs_spread"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols))

    # Filters and summary
    filters_col, summary_col = st.columns([1, 2])

    # Filters
    with filters_col:
        filtered = df.copy()

        if "week" in filtered.columns:
            filtered["week"] = pd.to_numeric(filtered["week"], errors="coerce").astype("Int64")
            weeks = sorted(filtered["week"].dropna().unique())
            if weeks:
                default_idx = len(weeks) - 1
                selected_week = st.selectbox("Week", weeks, index=default_idx)
                filtered = filtered[filtered["week"] == selected_week]

        # Team filter removed per request
        # Confidence slider removed per request

    # Show only future games if scores exist
    if "home_score" in filtered.columns:
        filtered = filtered[filtered["home_score"].isna()]

    # Summary metrics
    with summary_col:
        st.subheader("At a glance")
        games_shown = len(filtered)
        avg_conf = filtered["spread_confidence"].mean() if "spread_confidence" in filtered else None
        avg_units = filtered["suggested_units"].mean() if "suggested_units" in filtered else None

        m1, m2, m3 = st.columns(3)
        m1.metric("Games shown", games_shown)
        m2.metric("Avg spread conf", f"{avg_conf:.1f}%" if avg_conf is not None else "--")
        m3.metric("Avg suggested units", f"{avg_units:.2f}" if avg_units is not None else "--")

    # Format for display (avoid "+.2f" placeholders by rendering strings with explicit signs)
    display_df = filtered.copy()
    plus_cols = [
        "predicted_spread", "sportsbook_home_spread",
        "projected_total_points",
        "edge_vs_spread", "edge_vs_total",
    ]
    for col in plus_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:+.2f}" if pd.notna(x) else "")

    percent_cols = ["spread_confidence", "total_confidence"]
    for col in percent_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "")

    two_dec_cols = ["spread_win_prob", "suggested_units", "sportsbook_total"]
    for col in two_dec_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")

    st.subheader("Predictions (Model vs Sportsbook)")
    display_cols = [
        "week", "kickoff_local", "matchup", "model_pick", "bet_side",
        "predicted_spread", "sportsbook_home_spread",
        "spread_confidence", "suggested_units",
        "projected_total_points", "sportsbook_total", "total_confidence", "total_pick",
    ]
    display_cols = [c for c in display_cols if c in display_df.columns]

    st.dataframe(
        display_df[display_cols],
        hide_index=True,
        use_container_width=True,
    )
