# Protify

[![DOI](https://zenodo.org/badge/999903920.svg)](https://doi.org/10.5281/zenodo.15701071)

Protify is a Python package for estimating stellar rotation periods from TESS light curves. It combines Lomb-Scargle periodogram analysis, custom light curve metrics, and a trained machine learning classifier to identify likely rotators.

The classifier is trained on benchmark gyrochronology open cluster stars and selected field stars from [Rampalli et al. (2023)](#citation), achieving a cross-validation accuracy of approximately 80%.

> If you use Protify in your work, **please cite both the Zenodo release and [Rampalli et al. (2023)](#citation).**

Original code written by Rayna Rampalli. This package was developed with the help of OpenAI tools to support testing and documentation.

---

## Dependencies

Protify requires:

- `numpy`
- `pandas`
- `scikit-learn`
- `lightkurve >= 2.0`
- `matplotlib`
- `astropy`
- `PyAstronomy`



---

## Input Requirements

Your input CSV must contain at least:

- A column labeled `TIC` with TESS Input Catalog IDs (integers only).

Optionally:

- A `gmag` column with Gaia G-band magnitudes (used by the classifier).

Other fields like `RA`, `Dec`, or provenance flags can be included but are not required.

---

## Installation & Quickstart

```bash
git clone https://github.com/RaynaRampalli/protify.git
cd protify
pip install -e .
```

After installation, use the CLI to run Protify in three stages:

```bash
# Step 1: Run the light curve processing and period analysis
protify run --input examples/sample_input.csv --raw rotation_raw.csv

# Step 2: Summarize per-sector metrics to derive final period estimates
protify summarize --raw rotation_raw.csv --summary rotation_summary.csv

# Step 3: Classify rotators using the trained model
protify classify --raw rotation_raw.csv --summary rotation_summary.csv --train protify/data/RotatorTrainingSet.csv
```

---
## ⚠️ Caveats

- **By-eye validation is recommended**. TESS systematics and short baselines increase false positive rates compared to Kepler/K2.
- This package is not optimized for speed. Expect ~5–15 seconds per sector on a 2020 MacBook Pro with all options enabled.
- `examples/sample_input.csv` contains known rotators from the training set and is only for demonstration.

---

## CLI Reference

After installing Protify, the `protify` command has three subcommands: `run`, `summarize`, and `classify`.

###  `protify run`

Downloads TESS light curves and computes rotation periodograms.

```bash
protify run \
  --input examples/sample_input.csv \
  --raw rotation_raw.csv \
  [--save-lc] \
  [--save-plots]
```

**Options:**
- `--input`: CSV with TIC IDs (**required**)
- `--raw`: Output CSV for raw sector-by-sector metrics
- `--save-lc`: Save light curves as `.pkl` files
- `--save-plots`: Save light curve + periodogram plots as PDFs

---

### `protify summarize`

Summarizes raw sector-level metrics into final rotation period estimates.

```bash
protify summarize \
  --raw rotation_raw.csv \
  [--summary rotation_summary.csv] \
  [--no-autoval]
```

**Options:**
- `--raw`: Raw CSV output from `protify run` (**required**)
- `--summary`: Output file for summary metrics (default: `rotation_summary.csv`)
- `--no-autoval`: Include all stars, not just auto-validated ones

---

### `protify classify`

Applies a trained classifier to flag likely rotators.

```bash
protify classify \
  --raw rotation_raw.csv \
  --summary rotation_summary.csv \
  --train protify/data/RotatorTrainingSet.csv \
  [--output rotation_classified.csv] \
  [--no-autoval]
```

**Options:**
- `--raw`: Raw metrics CSV (**required**)
- `--summary`: Summary metrics CSV (**required**, can reuse from above)
- `--train`: Training set CSV (**required**)
- `--output`: Output file for classification results (default: `rotation_classified.csv`)
- `--no-autoval`: Include all stars, not just auto-validated ones as determined in  `protify summarize` (e.g., stars with significant rotation signals and matching periods for > 2/3 of all observed sectors)

If `AutoVal?` is **not present**, all stars in the file will be classified regardless of this flag.

---

#### Required Columns for Classification

If you are not using the full pipeline (`protify run` and `protify summarize`), your `--summary` CSV **must** include the following columns:

| Column    | Description                                                                 |
|-----------|-----------------------------------------------------------------------------|
| `prot`    | Final rotation period (in days), usually from multiple sector detections    |
| `func`    | Fractional uncertainty on the period: `uncertainty / prot`                  |
| `snr`     | Average signal-to-noise ratio across sectors — defined as `peak power / median power` |
| `mpower`  | Average of median periodogram power across all sectors                      |

> **Note:** The values of `snr` and `mpower` may vary depending on the periodogram method + software used. For compatibility with the trained model, we recommend generating them using `protify run` followed by `protify summarize`.


---

## Examples

The `examples/` directory includes:

- `sample_input.csv` — demo input stars (from the training set, do not use for real science).
- `demo_pipeline.ipynb` — step-by-step Jupyter Notebook showcasing pipeline usage.




---



## Data Sources

Protify downloads light curves from the **TESS mission**, filtering for:

- SPOC
- TESS-SPOC
- QLP

It prioritizes `PDCSAP_FLUX`, with fallbacks to `SAP_FLUX` or raw `flux`. Light curves are normalized and NaNs removed before periodogram analysis.

---

## Citation

If you use Protify, please cite the software release **and** the associated paper:

### Software Citation

Rayna Rampalli. (2025). *Protify: A rotation period pipeline for TESS light curves* (v0.1.1) [Software]. Zenodo.  
[https://doi.org/10.5281/zenodo.15701072](https://doi.org/10.5281/zenodo.15701072)

```bibtex
@software{protify_v011,
  author       = {Rampalli, Rayna},
  title        = {Protify: A rotation period pipeline for TESS light curves},
  version      = {v0.1.1},
  year         = 2025,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.15701072},
  url          = {https://doi.org/10.5281/zenodo.15701072}
}
```

### Paper Citation

**Rampalli et al. (2023)**  
*Wrinkles in Time. I. Rapid Rotators Found in High-eccentricity Orbits*  
ApJ, 958, 76  
[ADS link](https://ui.adsabs.harvard.edu/abs/2023ApJ...958...76R) | [arXiv:2310.02305](https://arxiv.org/abs/2310.02305)

```bibtex
@ARTICLE{2023ApJ...958...76R,
       author = {{Rampalli}, Rayna and {Smock}, Amy and {Newton}, Elisabeth R. and {Daniel}, Kathryne J. and {Curtis}, Jason L.},
        title = "{Wrinkles in Time. I. Rapid Rotators Found in High-eccentricity Orbits}",
      journal = {\apj},
     keywords = {Stellar rotation, Milky Way dynamics, Stellar kinematics, Stellar ages, 1629, 1051, 1608, 1581},
         year = 2023,
        month = nov,
       volume = {958},
       number = {1},
          eid = {76},
        pages = {76},
          doi = {10.3847/1538-4357/acff69},
archivePrefix = {arXiv},
       eprint = {2310.02305},
 primaryClass = {astro-ph.SR}
}
```

---
