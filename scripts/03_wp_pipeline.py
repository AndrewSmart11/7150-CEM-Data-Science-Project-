#!/usr/bin/env python3
"""
Compute placeholder WP series, calibration curves, toy "optimized" WP,
and save enriched CSVs and plots.
Usage:
  python 03_wp_pipeline.py --indir outputs --outdir outputs/wp_outputs
"""
import os, math, argparse
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

def predict_wp_placeholder(row: pd.Series) -> float:
    if row["innings"] != 2:
        return np.nan
    crr = row.get("CRR", np.nan)
    rrr = row.get("RRR", np.nan)
    wkts = row.get("innings_wkts", np.nan)
    balls_rem = row.get("balls_remaining", np.nan)
    runs_rem = row.get("runs_remaining", np.nan)
    if isinstance(runs_rem, (int, float)) and runs_rem == 0:
        return 1.0
    if isinstance(balls_rem, (int, float)) and balls_rem == 0 and runs_rem and runs_rem > 0:
        return 0.0
    crr = 0.0 if pd.isna(crr) else crr
    rrr = 0.0 if pd.isna(rrr) else rrr
    wkts = 0.0 if pd.isna(wkts) else wkts
    margin = crr - rrr
    wickets_term = max(0.0, 10.0 - wkts) / 10.0
    if wkts >= 6: wickets_term *= 0.8
    over = row.get("over", 1)
    phase_bonus = 0.00 if over <= 6 else (0.05 if over <= 15 else -0.03)
    z = 0.8 * margin + 0.6 * (wickets_term - 0.5) + phase_bonus
    wp = 1 / (1 + math.exp(-z))
    if runs_rem is not None and balls_rem is not None and balls_rem > 0:
        if runs_rem <= 6: wp = min(1.0, wp + 0.06)
        if runs_rem <= 3: wp = min(1.0, wp + 0.06)
    return float(np.clip(wp, 0.0, 1.0))

def compute_wp_series(df):
    ch = df[df["innings"] == 2].copy()
    ch["wp_pred"] = ch.apply(predict_wp_placeholder, axis=1)
    winner_is_batting2 = (ch["runs_remaining"] == 0).any()
    ch["won_eventual"] = 1 if winner_is_batting2 else 0
    return ch

def calibration_curve_df(df_wp, n_bins=10):
    x = df_wp["wp_pred"].values; y = df_wp["won_eventual"].values
    bins = np.linspace(0, 1, n_bins+1)
    idx = np.clip(np.digitize(x, bins, right=False) - 1, 0, n_bins-1)
    rows = []
    for b in range(n_bins):
        mask = idx == b
        if not mask.any():
            rows.append({"bin_mid": 0.05 + 0.1*b, "pred_mean": np.nan, "obs_rate": np.nan, "count": 0})
            continue
        rows.append({
            "bin_mid": 0.05 + 0.1*b,
            "pred_mean": float(np.nanmean(x[mask])),
            "obs_rate": float(np.nanmean(y[mask])),
            "count": int(mask.sum()),
        })
    return pd.DataFrame(rows)

def make_toy_optimized_wp(df_wp):
    opt = df_wp.copy()
    opt["wp_opt"] = opt["wp_pred"]
    mid_mask = (opt["over"].between(7, 15)) & (opt["RRR"] > opt["CRR"])
    opt.loc[mid_mask, "wp_opt"] = np.clip(opt.loc[mid_mask, "wp_opt"] + 0.03, 0, 1)
    death_mask = (opt["over"] >= 16) & (opt["RRR"] > opt["CRR"])
    opt.loc[death_mask, "wp_opt"] = np.clip(opt.loc[death_mask, "wp_opt"] + 0.02, 0, 1)
    opt["wp_delta"] = opt["wp_opt"] - opt["wp_pred"]
    return opt

def plot_calibration(cal_df, title, save_path):
    plt.figure(figsize=(5,5))
    plt.plot([0,1], [0,1], "--", label="Perfect calibration")
    mask = cal_df["count"] > 0
    plt.plot(cal_df.loc[mask, "pred_mean"], cal_df.loc[mask, "obs_rate"], marker="o", label="Model")
    plt.xlabel("Predicted WP"); plt.ylabel("Observed Win Rate")
    plt.title(title); plt.grid(True, linestyle="--", alpha=0.6); plt.legend(); plt.tight_layout()
    plt.savefig(save_path, dpi=200); plt.close()

def plot_wp_timeline(df_wp, title, save_path):
    x = np.arange(len(df_wp))
    plt.figure(figsize=(9,4)); plt.plot(x, df_wp["wp_pred"], label="WP (placeholder)")
    if "wp_opt" in df_wp.columns: plt.plot(x, df_wp["wp_opt"], label="WP (toy optimized)")
    plt.xlabel("Delivery index (2nd innings)"); plt.ylabel("Win Probability")
    plt.title(title); plt.grid(True, linestyle="--", alpha=0.6); plt.legend(); plt.tight_layout()
    plt.savefig(save_path, dpi=200); plt.close()

def plot_delta_hist(df_wp, title, save_path):
    if "wp_delta" not in df_wp.columns: return
    plt.figure(figsize=(5,4)); plt.hist(df_wp["wp_delta"].dropna().values, bins=20)
    plt.xlabel("ΔWP (optimized − actual)"); plt.ylabel("Count"); plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.6); plt.tight_layout(); plt.savefig(save_path, dpi=200); plt.close()

def process_file(infile, outdir):
    df = pd.read_csv(infile).sort_values(["innings","over","ball_in_over"]).reset_index(drop=True)
    df_wp = compute_wp_series(df)
    cal = calibration_curve_df(df_wp, n_bins=10)
    df_opt = make_toy_optimized_wp(df_wp)

    base = os.path.splitext(os.path.basename(infile))[0]
    os.makedirs(outdir, exist_ok=True)
    df_opt.to_csv(os.path.join(outdir, f"{base}_wp_enriched.csv"), index=False)
    plot_calibration(cal, f"Calibration – {base}", os.path.join(outdir, f"{base}_calibration.png"))
    plot_wp_timeline(df_opt, f"WP Timeline – {base}", os.path.join(outdir, f"{base}_timeline.png"))
    plot_delta_hist(df_opt, f"ΔWP Histogram – {base}", os.path.join(outdir, f"{base}_delta_hist.png"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", type=str, default="outputs", help="Folder with *_features.csv files")
    ap.add_argument("--outdir", type=str, default="outputs/wp_outputs", help="Where to write enriched files & plots")
    args = ap.parse_args()
    files = [os.path.join(args.indir, f) for f in os.listdir(args.indir) if f.endswith("_features.csv")]
    for f in files:
        process_file(f, args.outdir)
    print("[OK] Wrote enriched CSVs and plots to", args.outdir)

if __name__ == "__main__":
    main()
