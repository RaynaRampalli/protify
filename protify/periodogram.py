import numpy as np
from scipy.signal import find_peaks
from astropy import modeling
from PyAstronomy.pyTiming import pyPeriod

def GLS(time, flux, error):
    clp = pyPeriod.Gls((time, flux, error), freq=np.arange(1/50, 1/0.097, 0.001))
    freq, power = clp.freq, clp.power
    pgramx = 1 / freq
    pgramy = power

    peaks2, _ = find_peaks(pgramy, height=0.5 * max(power))
    potpers = pgramx[peaks2]
    potpwrs = pgramy[peaks2]

    ifmax = np.argmax(power)
    p_freq = freq[ifmax]
    p_per = 1. / p_freq

    # Alias handling
    fp = np.where((potpers > 1.7 * p_per) & (potpers < 2.3 * p_per))[0]
    if len(fp) > 0:
        proti = potpers[fp[0]]
        pwri = potpwrs[fp[0]]
        if proti > 18:
            prot = p_per
            f_power = power[ifmax]
            lgpeakflag = 1.5
        elif p_per > 28:
            prot = proti
            f_power = pwri
            lgpeakflag = 0
        else:
            prot = proti
            f_power = pwri
            lgpeakflag = 0.5
    else:
        prot = p_per
        f_power = power[ifmax]
        lgpeakflag = 1

    # Adjust for long-period spurious peaks
    if p_per > 18 and len(potpers) > 0:
        idx_o = np.where(potpers < 18)
        if len(idx_o[0]) > 0:
            otherpers = potpers[idx_o]
            otherpwrs = potpwrs[idx_o]
            prot = np.sort(otherpers)[-1]
            f_power = otherpwrs[np.argsort(otherpers)][-1]
            lgpeakflag = 0

    return freq, pgramx, pgramy, prot, peaks2, ifmax, f_power, np.median(power), lgpeakflag

def unc_fit(freq, pgramy, prot):
    try:
        idp = (np.abs(freq - 1 / prot)).argmin()
        xunc = freq[idp - 30:idp + 30]
        yunc = pgramy[idp - 30:idp + 30]

        fitter = modeling.fitting.LevMarLSQFitter()
        model = modeling.models.Gaussian1D(pgramy[idp], freq[idp], 0.1 * freq[idp])
        fitted_model = fitter(model, xunc, yunc)

        ll = fitted_model.mean.value - fitted_model.stddev.value
        mu = fitted_model.mean.value
        ul = fitted_model.mean.value + fitted_model.stddev.value

        d1 = (1 / ll) - (1 / mu)
        d2 = (1 / mu) - (1 / ul)
        unc = max([d1, d2])

        return xunc, fitted_model(xunc), unc
    except Exception:
        return np.nan, np.nan, np.nan

def compute_rotation_metrics(lightcurves, sectors, tic_id):
    results = {}
    pgramx_list, pgramy_list, times, fluxes = [], [], [], []

    for i, lc in enumerate(lightcurves):
        time = lc.time.value
        flux = lc.flux.value
        flux_err = lc.flux_err.value if hasattr(lc, 'flux_err') else np.ones_like(flux)

        mask = np.isfinite(time) & np.isfinite(flux)
        time, flux, flux_err = time[mask], flux[mask], flux_err[mask]
        if len(time) < 10:
            continue

        try:
            freq, pgramx, pgramy, prot, peaks2, ifmax, power, medp, peakflag = GLS(time, flux, flux_err)
            _, _, unc = unc_fit(freq, pgramy, prot)
        except Exception:
            prot, unc, power, medp, peakflag = np.nan, np.nan, np.nan, np.nan, np.nan

        results[str(i)] = {
            'sector': str(sectors[i]),
            'prot': prot,
            'uncsec': unc,
            'power': power,
            'medpower': medp,
            'peakflag': peakflag
        }

        times.append(time)
        fluxes.append(flux)
        pgramx_list.append(pgramx)
        pgramy_list.append(pgramy)

    flat_result = {f"{i}_{k}": v for i, res in results.items() for k, v in res.items()}
    flat_result['TIC'] = tic_id  # top-level key used by runner.py

    return {
        'TIC': tic_id,
        'Times': times,
        'Fluxes': fluxes,
        'Pgramx': pgramx_list,
        'Pgramy': pgramy_list,
        'Sectors': sectors,
        'Results': results,
        'FlatResult': flat_result
    }
