from lightkurve import search_lightcurve
from lightkurve.lightcurve import LightCurve

def download_tess_lightcurves(tic_id, mission='TESS'):
    try:
        int(tic_id)
    except ValueError:
        print(f"Warning: ID '{tic_id}' is not a valid TIC integer. Results may be unreliable.")

    search = search_lightcurve(f"TIC {tic_id}", mission=mission)
    search_filtered = search[
        (search.author == 'SPOC') |
        (search.author == 'TESS-SPOC') |
        (search.author == 'QLP')
    ]

    if len(search_filtered) == 0:
        raise ValueError(f"No SPOC/QLP light curves found for TIC {tic_id}.")

    lcs, sectors = [], []
    for res in search_filtered:
        try:
            downloaded = res.download()
            if downloaded is None:
                raise ValueError("Downloaded object is None.")

            tclass = downloaded.__class__.__name__
            lc = None

            if tclass == "TessLightCurveFile":
                if hasattr(downloaded, "PDCSAP_FLUX") and downloaded.PDCSAP_FLUX is not None:
                    lc = downloaded.PDCSAP_FLUX
                elif hasattr(downloaded, "SAP_FLUX") and downloaded.SAP_FLUX is not None:
                    lc = downloaded.SAP_FLUX

            elif isinstance(downloaded, LightCurve):
                lc = downloaded

            if lc is None and hasattr(downloaded, "flux") and downloaded.flux is not None:
                lc = downloaded

            if lc is None:
                raise ValueError("No usable flux (PDCSAP, SAP, or raw flux) found.")

            lc = lc.remove_nans().normalize()

            # Handle sector robustly
            sector = res.mission[0] if hasattr(res, "mission") else None

            lcs.append(lc)
            sectors.append(sector)

        except Exception as e:
            print(f"Failed to download TIC {tic_id}: {e}")

    if len(lcs) == 0:
        raise ValueError(f"No usable light curves found for TIC {tic_id} after filtering.")

    return lcs, sectors
