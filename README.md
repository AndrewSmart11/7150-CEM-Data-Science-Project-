
> **CI Status**  
> ![CI](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/ci.yml/badge.svg) ·
> ![Pipeline](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/pipeline.yml/badge.svg)


# T20I Tactical Analytics (Git Repo)

This is a ready-to-init Git repository with a `pyproject.toml` for packaging and CLI entry points.

## Quickstart

```bash
# (optional) create & activate a virtualenv
python -m venv .venv && source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# install in editable mode
pip install -U pip
pip install -e .

# initialize git and make the first commit
git init
git add .
git commit -m "Initial commit: t20i tactical analytics"
```

### CLI Usage (after `pip install -e .`)
```bash
t20-extract --zip data/raw/t20s_json.zip --outdir data/processed
t20-features --indir data/processed --outdir data/processed
t20-wp --indir data/processed --outdir outputs/figures
t20-fig-indpak --infile outputs/tables/IND_PAK_2022_T20WC_ball_by_ball_features_wp_enriched.csv
```

# T20I Tactical Analytics (Refactored)

A tidy, reproducible layout separating code, data, outputs, and reports.

## Structure
```
t20i_tactical_analytics_refactored/
├─ scripts/                   # runnable scripts
│  ├─ 01_extract_matches.py
│  ├─ 02_build_features.py
│  ├─ 03_wp_pipeline.py
│  └─ 04_figures_ind_pak.py
├─ src/t20/                   # package scaffold for reusable modules
├─ data/
│  ├─ raw/                    # source files (e.g., Cricsheet zip)
│  └─ processed/              # intermediate CSVs (ball-by-ball, features)
├─ outputs/
│  ├─ tables/                 # final CSVs (e.g., *_wp_enriched.csv)
│  └─ figures/                # plots (calibration, timelines, ΔWP, Figure X/Y)
├─ models/                    # trained models & metrics (future)
└─ reports/
   └─ report.md               # short summary
```

## Reproduce
From the project root:

1. **Extract matches**
```bash
python scripts/01_extract_matches.py --zip data/raw/t20s_json.zip --outdir data/processed
```

2. **Build features**
```bash
python scripts/02_build_features.py --indir data/processed --outdir data/processed
```

3. **WP pipeline (enriched CSVs + figures)**
```bash
python scripts/03_wp_pipeline.py --indir data/processed --outdir outputs/figures
```
> Enriched CSVs are written alongside figures into `outputs/figures` by default in the script;
> in this bundle we've moved enriched CSVs to `outputs/tables/` for cleanliness.

4. **India–Pakistan 2022 figures**
```bash
python scripts/04_figures_ind_pak.py --infile outputs/tables/IND_PAK_2022_T20WC_ball_by_ball_features_wp_enriched.csv
```

## Notes
- The current WP is a **placeholder heuristic** to visualize pipelines; swap with your trained models later.
- Place your trained artifacts under `models/` and refactor scripts to load them when ready.
