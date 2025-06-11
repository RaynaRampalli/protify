
import pandas as pd
from protify.downloader import download_tess_lightcurves
from protify.periodogram import compute_rotation_metrics

def run_period_pipeline(input_csv, output_csv, save_lc_pickle=False, pickle_dir='lightcurves'):
    df = pd.read_csv(input_csv)
    results = []

    for index, row in df.iterrows():
        star_id = row.get('TIC') or row.get('ID')
        if pd.isnull(star_id):
            continue
        try:
            lcs, sectors = download_tess_lightcurves(star_id)
            metrics = compute_rotation_metrics(lcs, sectors, star_id)

            if save_lc_pickle:
                import os, pickle
                os.makedirs(pickle_dir, exist_ok=True)
                pickle_path = f"{pickle_dir}/TIC{star_id}.pkl"
                with open(pickle_path, 'wb') as f:
                    pickle.dump(metrics, f)

            result_row = {f"{i}_{k}": v for i, res in metrics['Results'].items() for k, v in res.items()}
            result_row['TIC'] = star_id
            results.append(result_row)

        except Exception as e:
            print(f"Failed on TIC {star_id}: {e}")

    pd.DataFrame(results).to_csv(output_csv, index=False)
