
from lightkurve import search_lightcurvefile

def download_tess_lightcurves(tic_id, mission='TESS'):
    search = search_lightcurvefile(f"TIC {tic_id}", mission=mission)
    lcf_collection = search.download_all()
    lcs, sectors = [], []
    for lcf in lcf_collection:
        lc = lcf.PDCSAP_FLUX.remove_nans().normalize()
        lcs.append(lc)
        sectors.append(lcf.sector)
    return lcs, sectors
