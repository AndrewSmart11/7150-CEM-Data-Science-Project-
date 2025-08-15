#!/usr/bin/env python3
"""
Produce:
 - Figure X: WP timeline – India vs Pakistan (MCG 2022)
 - Figure Y: ΔWP histogram – India vs Pakistan (MCG 2022)
Usage:
  python 04_figures_ind_pak.py --infile outputs/wp_outputs/IND_PAK_2022_T20WC_ball_by_ball_features_wp_enriched.csv
"""
import os, argparse
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", type=str, required=True)
    ap.add_argument("--outdir", type=str, default=None)
    args = ap.parse_args()
    infile = args.infile
    outdir = args.outdir or os.path.dirname(infile)
    os.makedirs(outdir, exist_ok=True)

    df = pd.read_csv(infile)
    ch = df[df["innings"] == 2].copy().sort_values(["over","ball_in_over"]).reset_index(drop=True)

    # Figure X
    fig_x = os.path.join(outdir, "figure_x_wp_timeline_ind_pak_2022.png")
    x = np.arange(len(ch))
    plt.figure(figsize=(10, 4.5))
    if "wp_pred" in ch.columns: plt.plot(x, ch["wp_pred"].values, label="WP (model)")
    if "wp_opt" in ch.columns:  plt.plot(x, ch["wp_opt"].values,  label="WP (optimized)")
    plt.xlabel("Delivery index (2nd innings)"); plt.ylabel("Win Probability")
    plt.title("Figure X: WP Timeline – India vs Pakistan (MCG 2022)")
    plt.grid(True, linestyle="--", alpha=0.6); plt.legend(); plt.tight_layout()
    plt.savefig(fig_x, dpi=200); plt.close()

    # Figure Y
    fig_y = os.path.join(outdir, "figure_y_delta_wp_histogram_ind_pak_2022.png")
    if "wp_delta" in ch.columns:
        deltas = ch["wp_delta"].dropna().values
    elif "wp_pred" in ch.columns:
        deltas = np.diff(ch["wp_pred"].values)
    else:
        deltas = np.array([0.0])
    plt.figure(figsize=(6.5, 4.2)); plt.hist(deltas, bins=20)
    plt.xlabel("ΔWP"); plt.ylabel("Count")
    plt.title("Figure Y: ΔWP Histogram – India vs Pakistan (MCG 2022)")
    plt.grid(True, linestyle="--", alpha=0.6); plt.tight_layout()
    plt.savefig(fig_y, dpi=200); plt.close()

    print("[OK] Saved:", fig_x)
    print("[OK] Saved:", fig_y)

if __name__ == "__main__":
    main()
