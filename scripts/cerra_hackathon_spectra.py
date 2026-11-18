"""Field panels and power spectra for the CERRA hackathon inference runs.

CERRA: the inference output holds the full 869 x 869 Lambert grid (5.4 km spacing,
written with max_num_targets=-1), so the spectrum is a radially averaged 2-D FFT on
the native grid (mean removed, Hann window). The SHT/FFT PSD in the evaluate package
needs a global or regular lat-lon grid and cannot be used here.

ERA5: spectra come from the evaluate package (psd metric, SHT) and are only
re-plotted here so both runs share one figure.

Usage: python scripts/cerra_hackathon_spectra.py <eval_dir> <out_dir>
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from omegaconf import OmegaConf

from weathergen.evaluate.io.wegen_reader import WeatherGenZarrReader

CERRA_RUNS = {
    "mxtyinf1": "CERRA, no FE",
    "je43inf1": "CERRA, FE",
    "rlufinf1": "CERRA+ERA5 input, no FE",
    "isk9inf1": "CERRA+ERA5 input, FE",
}
ERA5_RUNS = {"gjwginf0": "ERA5 only, no FE", "dwu8inf0": "ERA5 only, FE"}
CERRA_CHANNELS = {"10si": "10 m wind speed [m/s]", "r_850": "relative humidity 850 hPa [%]"}
DX_KM = 5.38  # measured mean grid spacing of the trimmed CERRA grid


def radial_psd(field: np.ndarray, dx_km: float) -> tuple[np.ndarray, np.ndarray]:
    """Radially averaged 2-D power spectrum of a square field; returns (wavelength km, power)."""
    n = field.shape[0]
    win = np.outer(np.hanning(n), np.hanning(n))
    f = (field - field.mean()) * win
    p = np.abs(np.fft.fftshift(np.fft.fft2(f))) ** 2 / (win**2).sum()
    ky, kx = np.indices(p.shape) - n // 2
    k = np.rint(np.hypot(kx, ky)).astype(int)
    kmax = n // 2
    sums = np.bincount(k.ravel(), weights=p.ravel())[1 : kmax + 1]
    counts = np.bincount(k.ravel())[1 : kmax + 1]
    wavenumber = np.arange(1, kmax + 1)
    return n * dx_km / wavenumber, sums / counts


def load_cerra(run_id: str):
    cfg = OmegaConf.create({"streams": {"CERRA": {"channels": list(CERRA_CHANNELS)}}})
    reader = WeatherGenZarrReader(cfg, run_id, None)
    out = reader.get_data("CERRA", fsteps=[1], channels=list(CERRA_CHANNELS))
    tgt, pred = out.target[1], out.prediction[1]
    n = int(round(np.sqrt(tgt.sizes["ipoint"])))
    t = tgt.transpose("sample", "channel", "ipoint").values.reshape(-1, len(CERRA_CHANNELS), n, n)
    p = pred.isel(ens=0).transpose("sample", "channel", "ipoint").values
    return t, p.reshape(t.shape), str(np.asarray(tgt["valid_time"].values).ravel()[0])[:16]


def main(eval_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    data = {r: load_cerra(r) for r in CERRA_RUNS}
    colors = dict(zip(CERRA_RUNS, ["C0", "C1", "C2", "C3"], strict=True))

    for ic, (ch, ch_label) in enumerate(CERRA_CHANNELS.items()):
        # --- field panels: target, then prediction and error for each run (sample 0)
        t0 = data["mxtyinf1"][0][0, ic]
        vmin, vmax = np.percentile(t0, [0.5, 99.5])
        emax = np.percentile(np.abs(data["je43inf1"][1][0, ic] - t0), 99)
        fig, axs = plt.subplots(2, 5, figsize=(22, 9), constrained_layout=True)
        im = axs[0, 0].imshow(t0, origin="lower", vmin=vmin, vmax=vmax, cmap="viridis")
        axs[0, 0].set_title(f"CERRA target\n{data['mxtyinf1'][2]}")
        axs[1, 0].axis("off")
        for j, (r, label) in enumerate(CERRA_RUNS.items(), start=1):
            p0 = data[r][1][0, ic]
            axs[0, j].imshow(p0, origin="lower", vmin=vmin, vmax=vmax, cmap="viridis")
            axs[0, j].set_title(f"{label}\n+3h prediction")
            ie = axs[1, j].imshow(p0 - t0, origin="lower", vmin=-emax, vmax=emax, cmap="RdBu_r")
            axs[1, j].set_title(
                f"prediction - target (RMSE {np.sqrt(((p0 - t0) ** 2).mean()):.2f})"
            )
        for ax in axs.ravel():
            ax.set_xticks([])
            ax.set_yticks([])
        fig.colorbar(im, ax=axs[0, :], shrink=0.8, label=ch_label)
        fig.colorbar(ie, ax=axs[1, :], shrink=0.8, label="error")
        fig.savefig(out_dir / f"cerra_fields_{ch}.png", dpi=110)
        plt.close(fig)

        # --- spectra, averaged over samples
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 9), sharex=True, height_ratios=[2, 1])
        psd_t = np.mean([radial_psd(f, DX_KM)[1] for f in data["mxtyinf1"][0][:, ic]], axis=0)
        wl = radial_psd(t0, DX_KM)[0]
        a1.loglog(wl, psd_t, "k", lw=2, label="CERRA target")
        for r, label in CERRA_RUNS.items():
            psd_p = np.mean([radial_psd(f, DX_KM)[1] for f in data[r][1][:, ic]], axis=0)
            a1.loglog(wl, psd_p, color=colors[r], label=label)
            a2.semilogx(wl, psd_p / psd_t, color=colors[r])
            ratio = lambda km: np.interp(km, wl[::-1], (psd_p / psd_t)[::-1])  # noqa: E731
            print(
                f"CERRA {ch} {r}: power ratio at "
                + ", ".join(f"{km} km {ratio(km):.2f}" for km in (300, 100, 50, 20, 12))
            )
        a1.invert_xaxis()
        a1.set_ylabel("power")
        a1.set_title(
            f"CERRA {ch}: radially averaged spectrum, +3h, {data['mxtyinf1'][0].shape[0]} samples"
        )
        a1.legend()
        a1.grid(True, which="both", alpha=0.3)
        a2.axhline(1, color="k", lw=0.8, ls="--")
        a2.set_ylim(0, 1.5)
        a2.set_ylabel("prediction / target")
        a2.set_xlabel("wavelength [km]")
        a2.grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / f"cerra_spectrum_{ch}.png", dpi=110)
        plt.close(fig)

    # --- ERA5 spectra from the evaluate package's psd scores
    fig, axs = plt.subplots(2, 3, figsize=(18, 9), sharex=True, height_ratios=[2, 1])
    for r, (color, label) in zip(
        ERA5_RUNS, [("C0", "ERA5 only, no FE"), ("C1", "ERA5 only, FE")], strict=True
    ):
        attrs = json.loads(
            (eval_dir / r / "evaluation" / f"{r}_ERA5_global_psd_chkpt00000.json").read_text()
        )["scores"][0]["attrs"]
        for j, ch in enumerate(["10u", "10v", "q_850"]):
            k = np.array(attrs[f"fstep_1/{ch}/frequencies"])
            t = np.array(attrs[f"fstep_1/{ch}/psd_target"])
            p = np.array(attrs[f"fstep_1/{ch}/psd_prediction"])
            if r == "gjwginf0":
                axs[0, j].loglog(k[1:], t[1:], "k", lw=2, label="ERA5 target")
            axs[0, j].loglog(k[1:], p[1:], color=color, label=label)
            axs[1, j].semilogx(k[1:], (p / t)[1:], color=color)
            axs[0, j].set_title(f"ERA5 {ch}: SHT spectrum, +3h")
            axs[1, j].axhline(1, color="k", lw=0.8, ls="--")
            axs[1, j].set_ylim(0, 1.5)
            axs[1, j].set_xlabel("total wavenumber")
            print(
                f"ERA5 {ch} {r}: power ratio at wavenumber 20 {(p / t)[20]:.2f}, 50 {(p / t)[50]:.2f}, 90 {(p / t)[90]:.2f}"
            )
    axs[0, 0].set_ylabel("power")
    axs[1, 0].set_ylabel("prediction / target")
    axs[0, 0].legend()
    for ax in axs.ravel():
        ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "era5_spectra.png", dpi=110)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
