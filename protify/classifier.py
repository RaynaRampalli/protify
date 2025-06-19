import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier


def run_classifier(input_file, train_file, output_file, use_autoval=True):
    df = pd.read_csv(input_file)
    train = pd.read_csv(train_file)

    # If requested, filter to AutoVal? == 1 stars
    if use_autoval and 'AutoVal?' in df.columns:
        df = df[df['AutoVal?'] == 1]

    # Map summary columns to classifier features if needed
    if 'FinalProt' in df.columns:
        df['prot'] = df['FinalProt']
    if 'FinalUnc' in df.columns:
        df['func'] = df['FinalUnc']
    if 'Detect' in df.columns and 'snr' not in df.columns:
        df['snr'] = df['Detect']  # crude proxy fallback
    if 'Sectors' in df.columns and 'mpower' not in df.columns:
        df['mpower'] = df['Sectors']  # crude proxy fallback

    # Determine feature columns from training set
    feature_cols = [col for col in train.columns if col not in ['rotate?', 'TIC', 'provenance', 'cluster', 'source_id']]
    train = train.dropna(subset=feature_cols + ['rotate?'])
    test = df.dropna(subset=feature_cols)

    if test.empty:
        print("Warning: no valid rows to classify after filtering.")
        df.to_csv(output_file, index=False)
        return

    X_train = train[feature_cols]
    y_train = train['rotate?']
    X_test = test[feature_cols]

    rf = RandomForestClassifier(n_estimators=450, max_depth=15)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1]  # Probability of being rotator

    df.loc[test.index, 'rotate?'] = y_pred
    df.loc[test.index, 'rotation_prob'] = y_prob

    # Print debug info
    print("\nClassification results (rotate? = 1 means rotator):")
    for i in test.index:
        tid = df.loc[i, "TIC"] if "TIC" in df.columns else i
        flag = df.loc[i, "rotate?"]
        prob = df.loc[i, "rotation_prob"]
        print(f"TIC {tid} | rotate?: {flag} | Prob: {prob:.3f}")
        if flag == 0:
            print(f"  ⚠️  Not flagged as rotator. Features:")
            print(df.loc[i, feature_cols])

    df.to_csv(output_file, index=False)

def generate_summary_from_raw(raw_csv_path, out_csv_path="rotation_summary.csv", autoval_only=True):
    import pandas as pd
    import numpy as np

    cc = pd.read_csv(raw_csv_path)
    snr = 40

    n_obs = max(int(col.split("_")[0]) for col in cc.columns if "_power" in col and col.split("_")[0].isdigit())

    for i in range(n_obs + 1):
        labels = (
            f"frac_{i}h", f"{i}_power", f"{i}_medpower", f"{i}_sig",
            f"{i}_uncsec", f"{i}_prot", f"{i}_fracuncsec", f"{i}_detect", f"{i}_sector"
        )
        cc[labels[0]] = pd.to_numeric(cc[labels[1]], errors="coerce") / pd.to_numeric(cc[labels[2]], errors="coerce")
        cc[labels[6]] = pd.to_numeric(cc[labels[4]], errors="coerce") / pd.to_numeric(cc[labels[5]], errors="coerce")
        cc[labels[7]] = (cc[labels[0]] >= snr) & (cc[labels[6]] <= 0.25)

    fprots, funcs, avals, match_counts, counts, sector_counts = [], [], [], [], [], []

    for j in cc.index:
        row = cc.loc[j]
        nanprots, nanuncs, allprots, alluncs = [], [], [], []
        count = 0
        sector_count = 0
        for i in range(min(n_obs + 1, 25)):
            if row.get(f"{i}_detect") == 1:
                nanprots.append(row.get(f"{i}_prot"))
                nanuncs.append(row.get(f"{i}_uncsec"))
                count += 1
            if isinstance(row.get(f"{i}_sector"), str):
                sector_count += 1
                allprots.append(row.get(f"{i}_prot"))
                alluncs.append(row.get(f"{i}_uncsec"))

        counts.append(count)
        sector_counts.append(sector_count)

        if count > 1:
            median = np.median(nanprots)
            median_unc = np.median(nanuncs)
            match_count, fprot_init, func_init = 0, [], []

            for prot_n, unc_n in zip(nanprots, nanuncs):
                frac = prot_n / median
                unci = np.sqrt((unc_n / prot_n) ** 2 + (median_unc / median) ** 2)
                unc = frac * unci

                if (frac - 2 * unc < 0.5 < frac + 2 * unc or
                    frac - 2 * unc < 2 < frac + 2 * unc or
                    (frac - 2 * unc < 1 < frac + 2 * unc) or
                    (round(frac, 0) == 1 and unci < 0.05)):
                    match_count += 1
                    fprot_init.append(median)
                    func_init.append(median_unc)
                else:
                    fprot_init.append(np.nan)
                    func_init.append(np.nan)

            match_counts.append(match_count)
            avals.append(int(match_count >= (2 / 3) * count))

            if np.all(np.isnan(fprot_init)):
                fprot = np.nan
                func = np.nan
                print(f"[WARN] All sector matches rejected for TIC {row.get('TIC', j)}")
            else:
                fprot = np.nanmax(fprot_init)
                func = func_init[np.nanargmax(fprot_init)]

        elif count == 1:
            fprot = nanprots[0]
            func = nanuncs[0]
            avals.append(0)
            match_counts.append(np.nan)

        else:
            fprot = np.median(allprots)
            func = np.median(alluncs)
            avals.append(np.nan)
            match_counts.append(np.nan)

        fprots.append(fprot)
        funcs.append(func)

    cc["FinalProt"] = fprots
    cc["FinalUnc"] = funcs
    cc["AutoVal?"] = avals
    cc["Detect"] = counts
    cc["Matches"] = match_counts
    cc["Sectors"] = sector_counts
    cc["ReliableDetection"] = cc["AutoVal?"] == 1  # ✅ New column

    valid_df = cc[cc["AutoVal?"] == 1] if autoval_only else cc.copy()

    # Add final mean metrics (renamed funcs → mean_funcs)
    snrs, powers, mpowers, mean_funcs = [], [], [], []
    for _, row in valid_df.iterrows():
        detects = []
        for i in range(n_obs + 1):
            try:
                if (row.get(f"{i}_power") / row.get(f"{i}_medpower", 1) >= snr and
                        row.get(f"{i}_fracuncsec", 1) <= 0.25):
                    detects.append(i)
            except:
                continue

        try:
            snrs.append(np.mean([row.get(f"{i}_power") / row.get(f"{i}_medpower", 1) for i in detects]) if detects else np.nan)
            powers.append(np.mean([row.get(f"{i}_power") for i in detects]) if detects else np.nan)
            mpowers.append(np.mean([row.get(f"{i}_medpower") for i in detects]) if detects else np.nan)
            mean_funcs.append(np.mean([row.get(f"{i}_fracuncsec") for i in detects]) if detects else np.nan)
        except:
            snrs.append(np.nan)
            powers.append(np.nan)
            mpowers.append(np.nan)
            mean_funcs.append(np.nan)

    valid_df["snr"] = snrs
    valid_df["power"] = powers
    valid_df["mpower"] = mpowers
    valid_df["func"] = mean_funcs
    valid_df["prot"] = valid_df["FinalProt"]

    if "gmag" not in valid_df.columns:
        valid_df["gmag"] = valid_df.get("phot_g_mean_mag", np.nan)

    summary_cols = ["gmag", "prot", "snr", "power", "mpower", "func"]
    summary_cols = [col for col in summary_cols if col in valid_df.columns]

    out_df = valid_df.dropna(subset=summary_cols)

    print("\nFinal summary per star:")
    for idx, row in out_df.iterrows():
        star_id = row.get("TIC", idx)
        try:
            print(f"{star_id} | Prot: {row['prot']:.3f} | SNR: {row['snr']:.2f} | "
                  f"Power: {row['power']:.2f} | MedPower: {row['mpower']:.2f} | "
                  f"FracUnc: {row['func']:.3f}")
        except Exception as e:
            print(f"{star_id} | Incomplete data: {e}")

    out_df.to_csv(out_csv_path, index=False)
    print(f"Saved summary to {out_csv_path}")
