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
    total = len(df)

    if os.path.exists(raw_output_csv):
        existing_df = pd.read_csv(raw_output_csv)
        done_ids = set(existing_df['TIC'].astype(str))
        existing_cols = list(existing_df.columns)
        print(f"Resuming: {len(done_ids)} stars already processed.")
    else:
        done_ids = set()
        existing_df = pd.DataFrame()
        existing_cols = []

    failed = []

    for index, row in df.iterrows():
        star_id = str(int(row.get('TIC')) or int(row.get('ID')))
        if pd.isnull(star_id) or star_id in done_ids:
            continue

        print(f"\n🔄 Processing {index + 1}/{total}: TIC {star_id}")

        try:
            start = time.time()

            lcs, sectors = download_tess_lightcurves(star_id)
            print(f"  Found {len(sectors)} sectors.")
            metrics = compute_rotation_metrics(lcs, sectors, star_id)

            if save_lc_pickle:
                os.makedirs(pickle_dir, exist_ok=True)
                with open(os.path.join(pickle_dir, f"TIC{star_id}.pkl"), "wb") as f:
                    pickle.dump(metrics, f)

            # Flatten sector-wise results
            flat_results = {}
            for i in sorted(metrics['Results'].keys(), key=int):
                sector_data = metrics['Results'][i]
                for key in ['sector', 'prot', 'uncsec', 'power', 'medpower', 'peakflag']:
                    colname = f"{i}_{key}"
                    flat_results[colname] = sector_data.get(key, None)

            result_row = {col: row[col] for col in row.index}
            result_row['TIC'] = star_id
            result_row.update(flat_results)

            # --- Sync columns and autosort ---
            for col in existing_cols:
                result_row.setdefault(col, None)
            for col in result_row.keys():
                if col not in existing_cols:
                    existing_cols.append(col)

            base_cols = ['TIC', 'ID', 'gmag']
            sector_cols = sorted(
                [col for col in existing_cols if col not in base_cols],
                key=lambda c: (int(c.split('_')[0]) if c[0].isdigit() else 9999, c)
            )
            sorted_cols = base_cols + [col for col in sector_cols if col not in base_cols]

            result_df = pd.DataFrame([result_row], columns=sorted_cols)
            existing_cols = sorted_cols  # keep updating column order

            # --- Write file ---
            if os.path.exists(raw_output_csv):
                result_df.to_csv(raw_output_csv, mode='a', header=False, index=False)
            else:
                result_df.to_csv(raw_output_csv, mode='w', header=True, index=False)

            print(f"  ✅ Saved TIC {star_id} to {raw_output_csv}")

            duration = round(time.time() - start, 2)
            if len(sectors) > 0:
                print(f"  Done in {duration}s (~{duration/len(sectors):.2f} s/sector)")
            else:
                print(f"  Done in {duration}s.")

        except Exception as e:
            print(f"❌ Failed on TIC {star_id}: {e}")
            failed.append({"TIC": star_id, "error": str(e)})
            pd.DataFrame(failed).to_csv(failure_log, index=False)

    if save_lc_pickle and save_plots:
        batch_plot_lightcurves(pickle_dir=pickle_dir, save_dir=plot_dir)
