import os
import pickle
import time
import pandas as pd

from protify.downloader import download_tess_lightcurves
from protify.periodogram import compute_rotation_metrics
from protify.plotting import batch_plot_lightcurves

def run_period_pipeline(
    input_csv,
    raw_output_csv,
    save_lc_pickle=False,
    pickle_dir='lightcurves',
    save_plots=False,
    plot_dir='plots',
    failure_log="failures.csv"
):
    df = pd.read_csv(input_csv)

    if os.path.exists(raw_output_csv):
        existing_df = pd.read_csv(raw_output_csv)
        done_ids = set(existing_df['TIC'].astype(str))
        print(f"Resuming: {len(done_ids)} stars already processed.")
    else:
        existing_df = pd.DataFrame()
        done_ids = set()

    failed = []
    updated_rows = []

    for index, row in df.iterrows():
        star_id = str(row.get('TIC') or row.get('ID'))
        if pd.isnull(star_id) or star_id in done_ids:
            continue

        try:
            start = time.time()
            print(f"Starting TIC {star_id}...")

            lcs, sectors = download_tess_lightcurves(star_id)
            print(f"  Found {len(sectors)} sectors.")
            metrics = compute_rotation_metrics(lcs, sectors, star_id)

            if save_lc_pickle:
                os.makedirs(pickle_dir, exist_ok=True)
                with open(os.path.join(pickle_dir, f"TIC{star_id}.pkl"), "wb") as f:
                    pickle.dump(metrics, f)

            # Always keep full set of sector columns (even if invalid)
            flat_results = {}
            for i in sorted(metrics['Results'].keys(), key=int):
                sector_data = metrics['Results'][i]
                for key in ['sector', 'prot', 'uncsec', 'power', 'medpower', 'peakflag']:
                    colname = f"{i}_{key}"
                    val = sector_data.get(key, None)
                    flat_results[colname] = val

            result_row = {col: row[col] for col in row.index}
            result_row['TIC'] = star_id
            result_row.update(flat_results)

            updated_rows.append(result_row)

            duration = round(time.time() - start, 2)
            if len(sectors) > 0:
                print(f"  Done in {duration}s (~{duration/len(sectors):.2f} s/sector)")
            else:
                print(f"  Done in {duration}s.")

        except Exception as e:
            print(f"❌ Failed on TIC {star_id}: {e}")
            failed.append({"TIC": star_id, "error": str(e)})
            pd.DataFrame(failed).to_csv(failure_log, index=False)

    # Combine old and new results, expanding all columns
    if updated_rows:
        new_df = pd.DataFrame(updated_rows)

        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
        else:
            combined_df = new_df

        combined_df.to_csv(raw_output_csv, index=False)
        print(f"\n✅ Saved all results to {raw_output_csv} with updated columns.")

    if save_lc_pickle and save_plots:
        batch_plot_lightcurves(pickle_dir=pickle_dir, save_dir=plot_dir)
