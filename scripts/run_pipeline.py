import argparse
from protify.runner import run_period_pipeline

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Input CSV with TIC IDs")
parser.add_argument("--raw", default="rotation_raw.csv", help="Output raw CSV")
parser.add_argument("--save-lc", action="store_true", help="Save light curve pickles")
parser.add_argument("--pickle-dir", default="lightcurves", help="Directory for light curve pickles")
parser.add_argument("--save-plots", action="store_true", help="Save validation plots")
parser.add_argument("--plot-dir", default="plots", help="Directory to save plots")

args = parser.parse_args()

run_period_pipeline(
    input_csv=args.input,
    raw_output_csv=args.raw,
    save_lc_pickle=args.save_lc,
    pickle_dir=args.pickle_dir,
    save_plots=args.save_plots,
    plot_dir=args.plot_dir
)
