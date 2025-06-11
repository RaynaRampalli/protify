import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

def _format_axes(ax):
    ax.tick_params(which='both', direction='in', width=2, bottom=True, top=True, left=True, right=True, pad=5)
    ax.tick_params(which='major', length=10, labelsize=20)
    ax.tick_params(which='minor', length=4)
    for axis in ['top', 'bottom', 'left', 'right']:
        ax.spines[axis].set_linewidth(2)
    ax.set_rasterization_zorder(0)

def plot_lightcurve_summary(times, fluxes, pgramxs, pgramys, prots, medps, powers, sectors, tic_ids, save_path=None):
    n = len(times)
    gs = gridspec.GridSpec(ncols=3, nrows=n)
    fig = plt.figure(figsize=(25, 5 * n))

    for i in range(n):
        time = times[i]
        flux = fluxes[i]
        pgramx = pgramxs[i]
        pgramy = pgramys[i]
        prot = prots[i]
        medp = medps[i]
        power = powers[i]
        sector = sectors[i]
        tic = tic_ids[i]

        if np.isnan(prot) or np.isnan(medp) or medp == 0:
            continue

        # Light curve
        ax = plt.subplot(gs[i, 0])
        ax.plot(time, flux, '.', label=sector, color='dodgerblue', zorder=-10)
        if i == n - 1:
            ax.set_xlabel('Time [days]', fontsize=25)
        ax.set_ylabel('Normalized Flux', fontsize=25)
        ax.legend(loc='upper right', fontsize=19)
        _format_axes(ax)

        # Periodogram
        ax = plt.subplot(gs[i, 1])
        ax.plot(pgramx, pgramy, 'k')
        ax.set_xscale('log')
        ax.axvline(prot, linewidth=5, color='orange', alpha=0.5,
                   label=rf'$P_{{\rm rot}}$ = {prot:.2f} d')
        ax.axhline(medp, linestyle='--', label='S/N: ' + str(int(power / medp)), color='mediumseagreen')
        if i == n - 1:
            ax.set_xlabel(r'$P_{\rm rot}$ [days]', fontsize=25)
        ax.set_ylabel('Power', fontsize=25)
        ax.set_title(f'TIC {tic}', fontsize=27)
        ax.legend(loc='upper left', fontsize=19)
        _format_axes(ax)

        # Phase plot
        phased_t = (time % prot) / prot
        ax = plt.subplot(gs[i, 2])
        ax.plot(phased_t, flux, '.', color='dodgerblue', zorder=-10)
        if i == n - 1:
            ax.set_xlabel('Phase', fontsize=25)
        ax.set_ylabel('Normalized Flux', fontsize=25)
        _format_axes(ax)

    plt.subplots_adjust(wspace=0.3, hspace=0.3)
    fig.align_labels()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
    return fig

def extract_sector_metrics(star_data, max_sectors=25):
    prots, medps, powers, uncs, snrs = [], [], [], [], []
    times, fluxes, pgramxs, pgramys, sectors = [], [], [], [], []
    for i in range(max_sectors):
        try:
            result = star_data["Results"][str(i)]
            prot = result['prot']
            medp = result['medpower']
            power = result['power']
            unc = result.get('uncsec', None)

            # Validation
            if (
                prot is None or np.isnan(prot) or prot >= 49 or
                medp is None or np.isnan(medp) or medp == 0 or
                power is None or np.isnan(power)
            ):
                continue

            # Append valid sector data
            prots.append(prot)
            medps.append(medp)
            powers.append(power)
            uncs.append(unc)
            snrs.append(power / medp)

            # Add corresponding arrays for plotting
            times.append(star_data["Times"][i])
            fluxes.append(star_data["Fluxes"][i])
            pgramxs.append(star_data["Pgramx"][i])
            pgramys.append(star_data["Pgramy"][i])
            sectors.append(star_data["Sectors"][i])

        except Exception:
            continue

    return prots, medps, powers, uncs, snrs, times, fluxes, pgramxs, pgramys, sectors

def batch_plot_lightcurves(pickle_dir, save_dir="plots", max_stars=None, combine_into_pdf=False, combined_pdf_name="protify_rotators.pdf"):
    from matplotlib.backends.backend_pdf import PdfPages

    os.makedirs(save_dir, exist_ok=True)
    files = sorted([f for f in os.listdir(pickle_dir) if f.endswith(".pkl")])
    if max_stars:
        files = files[:max_stars]

    pdf_path = os.path.join(save_dir, combined_pdf_name)
    pdf = PdfPages(pdf_path) if combine_into_pdf else None

    for file in files:
        with open(os.path.join(pickle_dir, file), "rb") as f:
            star_data = pickle.load(f)

        try:
            prots, medps, powers, uncs, snrs, times, fluxes, pgramxs, pgramys, sectors = extract_sector_metrics(star_data)
            if not prots:
                print(f"Skipped {file}: no valid sectors.")
                continue

            fig = plot_lightcurve_summary(
                times=times,
                fluxes=fluxes,
                pgramxs=pgramxs,
                pgramys=pgramys,
                prots=prots,
                medps=medps,
                powers=powers,
                sectors=sectors,
                tic_ids=[star_data["TIC"]] * len(prots),
                save_path=None if combine_into_pdf else os.path.join(save_dir, f"TIC{star_data['TIC']}_validation.pdf")
            )
            if combine_into_pdf:
                pdf.savefig(fig)
                plt.close(fig)
            else:
                plt.close(fig)

        except Exception as e:
            print(f"Failed to plot {file}: {e}")

    if combine_into_pdf:
        pdf.close()
        print(f"Combined PDF saved to {pdf_path}")
