# Convenience tasks
.PHONY: all extract features wp figures

all: extract features wp figures

extract:
	python scripts/01_extract_matches.py --zip data/raw/t20s_json.zip --outdir data/processed

features:
	python scripts/02_build_features.py --indir data/processed --outdir data/processed

wp:
	python scripts/03_wp_pipeline.py --indir data/processed --outdir outputs/figures

figures:
	python scripts/04_figures_ind_pak.py --infile outputs/tables/IND_PAK_2022_T20WC_ball_by_ball_features_wp_enriched.csv
