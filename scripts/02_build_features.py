#!/usr/bin/env python3
"""
Build match-state features for the extracted ball-by-ball CSVs.
Usage:
  python 02_build_features.py --indir outputs --outdir outputs
"""
import os, argparse
import numpy as np
import pandas as pd

def phase_from_over(over):
    if 1 <= over <= 6:
        return "powerplay"
    if 7 <= over <= 15:
        return "middle"
    return "death"

def add_match_state_features(df):
    df = df.copy()
    for col in ["innings","over","ball_in_over","runs_batter","runs_extras","runs_total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df.sort_values(["innings","over","ball_in_over"], inplace=True, ignore_index=True)
    df["phase"] = df["over"].apply(phase_from_over)
    df["extras_type"] = df["extras_type"].fillna("")
    df["legal_ball"] = ~df["extras_type"].str.lower().eq("wides")
    df["wicket_event"] = df["wicket_event"].astype(bool)
    df["innings_runs"] = df.groupby("innings")["runs_total"].cumsum()
    df["innings_wkts"] = df.groupby("innings")["wicket_event"].cumsum()
    df["balls_bowled_legal"] = df.groupby("innings")["legal_ball"].cumsum()
    df["balls_remaining"] = 120 - df["balls_bowled_legal"]

    first_innings_total = df.loc[df["innings"] == 1, "runs_total"].sum()
    target_to_win = first_innings_total + 1
    df["target_runs"] = np.where(df["innings"] == 2, target_to_win, np.nan)
    df["runs_remaining"] = np.where(
        df["innings"] == 2, np.maximum(target_to_win - df["innings_runs"], 0), np.nan
    )
    safe_balls = df["balls_bowled_legal"].replace(0, np.nan)
    df["CRR"] = (df["innings_runs"] * 6.0) / safe_balls
    safe_rem_balls = df["balls_remaining"].replace(0, np.nan)
    df["RRR"] = np.where(
        df["innings"] == 2,
        (df["runs_remaining"] * 6.0) / safe_rem_balls,
        np.nan
    )
    for col in ["CRR","RRR"]:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", type=str, default="outputs", help="Folder with ball-by-ball CSVs")
    ap.add_argument("--outdir", type=str, default="outputs", help="Where to write *_features.csv")
    args = ap.parse_args()

    files = [f for f in os.listdir(args.indir) if f.endswith("_ball_by_ball.csv")]
    for fname in files:
        df = pd.read_csv(os.path.join(args.indir, fname))
        feat_df = add_match_state_features(df)
        name, _ = os.path.splitext(fname)
        out_path = os.path.join(args.outdir, f"{name}_features.csv")
        feat_df.to_csv(out_path, index=False, encoding="utf-8")
        print("[OK] Wrote:", out_path, "(rows:", len(feat_df), ")")

if __name__ == "__main__":
    main()
