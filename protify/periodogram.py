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

def get_unmasked_array(q):
    if isinstance(q, Masked):
        return q.unmasked.value.astype(np.float64)
    else:
        return q.value.astype(np.float64)

def compute_rotation_metrics(lightcurves, sectors, tic_id):
    print(f"Starting TIC {tic_id} with {len(lightcurves)} lightcurves")
    
    results = {}
    pgramx_list, pgramy_list, times, fluxes = [], [], [], []

    for i, lc in enumerate(lightcurves):
        print(f"\n--- Sector {i} ---")

        try:
            time = lc.time.value
            print(f"  Time array loaded: len={len(time)}")

            flux = get_unmasked_array(lc.flux)
            print(f"  Flux array loaded")

            if hasattr(lc, 'flux_err'):
                flux_err = get_unmasked_array(lc.flux_err)
                print(f"  Flux error loaded from lc")
            else:
                flux_err = np.ones_like(flux)
                print(f"  Flux error defaulted to ones")

            mask = np.isfinite(time) & np.isfinite(flux)
            time, flux, flux_err = time[mask], flux[mask], flux_err[mask]
            print(f"  After masking: len(time) = {len(time)}")

            if len(time) < 10:
                print(f"  Skipping sector {i}: not enough data points")
                continue

            print(f"  Running GLS...")
            freq, pgramx, pgramy, prot, peaks2, ifmax, power, medp, peakflag = GLS(time, flux, flux_err)
            print(f"  GLS complete. Period = {prot:.2f}")

            print(f"  Running unc_fit...")
            _, _, unc = unc_fit(freq, pgramy, prot)
            print(f"  unc_fit complete. Unc = {unc:.2f}")

        except Exception as e:
            print(f"  ERROR in sector {i} for TIC {tic_id}: {e}")
            prot, unc, power, medp, peakflag = np.nan, np.nan, np.nan, np.nan, np.nan
            freq, pgramx, pgramy = None, None, None

        # Get safe sector label
        if sectors is None:
            print(f"  ERROR: sectors is None!")
            sector_val = f"UNKNOWN_{i}"
        elif i >= len(sectors):
            print(f"  ERROR: sector index {i} out of bounds for sectors of length {len(sectors)}")
            sector_val = f"UNKNOWN_{i}"
        elif sectors[i] is None:
            print(f"  WARNING: sectors[{i}] is None")
            sector_val = f"UNKNOWN_{i}"
        else:
            sector_val = str(sectors[i])

        results[str(i)] = {
            'sector': sector_val,
            'prot': prot,
            'uncsec': unc,
            'power': power,
            'medpower': medp,
            'peakflag': peakflag
        }

        times.append(time)
        fluxes.append(flux)
        if pgramx is not None and pgramy is not None:
            pgramx_list.append(pgramx)
            pgramy_list.append(pgramy)

        print(f"  Sector {i} finished.")

    print("All sectors processed. Finalizing...")

    flat_result = {f"{i}_{k}": v for i, res in results.items() for k, v in res.items()}
    flat_result['TIC'] = tic_id

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
