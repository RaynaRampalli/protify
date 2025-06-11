
from astropy.timeseries import LombScargle
import numpy as np

def compute_rotation_metrics(lightcurves, sectors, tic_id):
    results = {}
    for i, lc in enumerate(lightcurves):
        time = lc.time.value
        flux = lc.flux.value

        mask = np.isfinite(time) & np.isfinite(flux)
        time, flux = time[mask], flux[mask]
        if len(time) < 10: continue

        freq = np.logspace(np.log10(1/40), np.log10(1/0.1), 10000)
        ls = LombScargle(time, flux)
        power = ls.power(freq)
        best_freq = freq[np.argmax(power)]
        prot = 1 / best_freq
        median_power = np.median(power)
        unc = 0.15 * prot  # placeholder uncertainty

        results[str(i)] = {
            'sector': str(sectors[i]),
            'prot': prot,
            'uncsec': unc,
            'power': power.max(),
            'medpower': median_power,
            'peakflag': int(power.max() > 5 * median_power)
        }

    return {
        'TIC': tic_id,
        'Times': [lc.time.value for lc in lightcurves],
        'Fluxes': [lc.flux.value for lc in lightcurves],
        'Pgramx': [1/freq for _ in lightcurves],
        'Pgramy': [LombScargle(lc.time.value, lc.flux.value).power(freq) for lc in lightcurves],
        'Sectors': sectors,
        'Results': results
    }
