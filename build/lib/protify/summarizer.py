
import pandas as pd
import numpy as np

def summarize_rotation_table(df, max_sectors=25):
    snr_threshold = 40
    summary = []

    for i, row in df.iterrows():
        detects, prot_vals, unc_vals = [], [], []
        for s in range(max_sectors):
            try:
                snr = row[f"{s}_power"] / row[f"{s}_medpower"]
                frac_unc = row[f"{s}_uncsec"] / row[f"{s}_prot"]
                if snr >= snr_threshold and frac_unc <= 0.25:
                    detects.append(s)
                    prot_vals.append(row[f"{s}_prot"])
                    unc_vals.append(row[f"{s}_uncsec"])
            except:
                continue

        if len(prot_vals) > 0:
            median_prot = np.median(prot_vals)
            median_unc = np.median(unc_vals)
        else:
            median_prot = np.nan
            median_unc = np.nan

        summary.append({
            'TIC': row['TIC'],
            'FinalProt': median_prot,
            'FinalUnc': median_unc,
            'Detect': len(detects)
        })

    return pd.DataFrame(summary)
