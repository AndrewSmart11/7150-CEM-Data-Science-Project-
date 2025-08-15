
import os, sys, argparse, runpy

def _run(path, argv):
    sys.argv = [path] + argv
    runpy.run_path(path, run_name="__main__")

def extract_main():
    _run(os.path.join(os.path.dirname(__file__), "01_extract_matches.py"), sys.argv[1:])

def features_main():
    _run(os.path.join(os.path.dirname(__file__), "02_build_features.py"), sys.argv[1:])

def wp_main():
    _run(os.path.join(os.path.dirname(__file__), "03_wp_pipeline.py"), sys.argv[1:])

def fig_indpak_main():
    _run(os.path.join(os.path.dirname(__file__), "04_figures_ind_pak.py"), sys.argv[1:])
