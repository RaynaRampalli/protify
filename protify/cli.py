import argparse
from protify.runner import run_period_pipeline
from protify.classifier import run_classifier, generate_summary_from_raw

def main():
    parser = argparse.ArgumentParser(prog="protify")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Run period-finding pipeline")
    run_parser.add_argument("--input", required=True, help="CSV file with TICs")
    run_parser.add_argument("--raw", required=True, help="Output CSV for raw sector-level metrics")
    run_parser.add_argument("--save-lc", action="store_true", help="Save light curves as pickles")
    run_parser.add_argument("--save-plots", action="store_true", help="Save light curve plots")

    # Subcommand: summarize
    sum_parser = subparsers.add_parser("summarize", help="Generate summary metrics from raw CSV")
    sum_parser.add_argument("--raw", required=True, help="Path to raw output CSV")
    sum_parser.add_argument("--summary", default="rotation_summary.csv", help="Output summary CSV")
    sum_parser.add_argument("--no-autoval", action="store_true", help="Include all stars regardless of AutoVal?")

    # Subcommand: classify
    classify_parser = subparsers.add_parser("classify", help="Classify stars as rotators or not")
    classify_parser.add_argument("--raw", required=True, help="Raw output CSV (for summary)")
    classify_parser.add_argument("--summary", required=True, help="Output summary CSV")
    classify_parser.add_argument("--train", required=True, help="Training set CSV")
    classify_parser.add_argument("--output", default="rotation_classified.csv", help="Output CSV for classified results")
    classify_parser.add_argument("--no-autoval", action="store_true", help="Include all stars regardless of AutoVal?")

    args = parser.parse_args()

    if args.command == "run":
        run_period_pipeline(
            input_csv=args.input,
            raw_output_csv=args.raw,
            save_lc_pickle=args.save_lc,
            save_plots=args.save_plots,
        )

    elif args.command == "summarize":
        generate_summary_from_raw(
            raw_csv_path=args.raw,
            out_csv_path=args.summary,
            autoval_only=not args.no_autoval,
        )

    elif args.command == "classify":
        generate_summary_from_raw(
            raw_csv_path=args.raw,
            out_csv_path=args.summary,
            autoval_only=not args.no_autoval,
        )
        run_classifier(
            input_file=args.summary,
            train_file=args.train,
            output_file=args.output,
            use_autoval=not args.no_autoval,
        )
