# NOTE: Deprecated. Use `generate_summary_from_raw()` in classifier.py instead.
import pandas as pd
import numpy as np

def summarize_rotation_table(df, max_sectors=25, snr_threshold=40, max_frac_unc=0.25):
    """
    Summarizes per-sector rotation period detections into final period metrics.

    Parameters:
        df (pd.DataFrame): Input DataFrame with sector-by-sector period results.
        max_sectors (int): Number of sectors to scan per star.
        snr_threshold (float): Minimum power-to-median-power threshold.
        max_frac_unc (float): Maximum allowed fractional uncertainty.

    Returns:
        pd.DataFrame: A summary DataFrame with TIC, FinalProt, FinalUnc, Detect, Sectors.
    """
    summary = []

    for i, row in df.iterrows():
        detects, prot_vals, unc_vals = [], [], []
        sector_count = 0

        for s in range(max_sectors):
            sector_col = f"{s}_sector"
            if sector_col in row and pd.notna(row[sector_col]):
                sector_count += 1

            try:
                snr = row[f"{s}_power"] / row[f"{s}_medpower"]
                frac_unc = row[f"{s}_uncsec"] / row[f"{s}_prot"]
                if snr >= snr_threshold and frac_unc <= max_frac_unc:
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
            'Detect': len(detects),
            'Sectors': sector_count
        })

    summary_df = pd.DataFrame(summary)

    # Join back onto original table for downstream classification
    merged = df.merge(summary_df, on="TIC", how="left")

    # Rename gmag if needed
    if "phot_g_mean_mag" in merged.columns and "gmag" not in merged.columns:
        merged["gmag"] = merged["phot_g_mean_mag"]

    return merged
