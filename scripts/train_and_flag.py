import argparse
import pandas as pd
from protify.classifier import run_classifier, generate_summary_from_raw

parser = argparse.ArgumentParser()
parser.add_argument("--raw", default="rotation_raw.csv", help="Input raw rotation CSV")
parser.add_argument("--summary", default="rotation_summary.csv", help="Generated summary CSV")
parser.add_argument("--output", default="rotation_flagged.csv", help="Output flagged CSV")
parser.add_argument("--train", default="protify/data/RotatorTrainingSet.csv", help="Training set CSV path")
parser.add_argument("--no_autoval", action="store_true", help="Disable filtering to AutoVal? == 1")

args = parser.parse_args()

# Step 1: Generate the summary CSV from raw output
generate_summary_from_raw(
    raw_csv_path=args.raw,
    out_csv_path=args.summary,
    autoval_only=not args.no_autoval
)

# Step 2: Run classifier using the new summary file
run_classifier(
    input_file=args.summary,
    train_file=args.train,
    output_file=args.output,
    use_autoval=not args.no_autoval
)
