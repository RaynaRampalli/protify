
import argparse
import pandas as pd
from protify.runner import run_period_pipeline
from protify.classifier import train_classifier, apply_classifier
from protify.plotting import batch_plot_lightcurves

def main():
    parser = argparse.ArgumentParser(prog='protify', description='Protify: Stellar rotation analysis from TESS')
    subparsers = parser.add_subparsers(dest='command')

    # ---- RUN COMMAND ----
    run_parser = subparsers.add_parser('run', help='Run rotation period detection')
    run_parser.add_argument('--input', required=True, help='Input CSV with TIC IDs')
    run_parser.add_argument('--output', default='rotation_raw.csv', help='Output CSV with sector metrics')
    run_parser.add_argument('--save-lc', action='store_true', help='Save light curves to .pkl files')
    run_parser.add_argument('--save-plots', action='store_true', help='Generate validation plots for each star')
    run_parser.add_argument('--pickle-dir', default='lightcurves', help='Where to store .pkl light curves')
    run_parser.add_argument('--plot-dir', default='plots', help='Where to save validation plots')

    # ---- CLASSIFY COMMAND ----
    classify_parser = subparsers.add_parser('classify', help='Train classifier and flag rotators')
    classify_parser.add_argument('--input', required=True, help='Input summarized CSV')
    classify_parser.add_argument('--output', default='rotation_flagged.csv', help='Output classified CSV')
    classify_parser.add_argument('--train', default='protify/data/RotatorTrainingSet.csv', help='Training set CSV')

    args = parser.parse_args()

    if args.command == 'run':
        run_period_pipeline(
            input_csv=args.input,
            output_csv=args.output,
            save_lc_pickle=args.save_lc,
            pickle_dir=args.pickle_dir
        )
        if args.save_plots:
            batch_plot_lightcurves(pickle_dir=args.pickle_dir, save_dir=args.plot_dir)

    elif args.command == 'classify':
        train_df = pd.read_csv(args.train)
        rf_model, acc = train_classifier(train_df)
        print(f"Training accuracy: {acc:.2f}")

        test_df = pd.read_csv(args.input)
        flagged_df = apply_classifier(rf_model, test_df)
        flagged_df.to_csv(args.output, index=False)
