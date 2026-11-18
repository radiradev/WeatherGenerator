"""Radially averaged power spectra of CERRA predictions and targets.

The inference output for CERRA is a random subset of the 5.5 km grid points
(max_num_targets), so the built-in PSD metric (SHT or regular lat-lon FFT)
does not apply. Here predictions and targets are linearly interpolated from the
same scattered points onto a regular 11 km grid in a Lambert conformal
projection, a Hann window is applied, and the 2-D FFT power is averaged in
rings of constant wavenumber. Interpolation damps the smallest scales for
predictions and targets alike, so wavelengths below about 50 km are indicative.

Usage: python scripts/cerra_hackathon_spectra.py OUT.png run_id=label [run_id=label ...]
"""

import sys

import cartopy.crs as ccrs
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from omegaconf import OmegaConf
from scipy.interpolate import LinearNDInterpolator

from weathergen.evaluate.io.wegen_reader import WeatherGenZarrReader

STREAM = "CERRA"
CHANNELS = ["10si", "r_850"]
DX_KM = 11.0
HALF_WIDTH_KM = 1800.0  # square box around the projection centre, inside the trimmed domain
PROJ = ccrs.LambertConformal(central_longitude=8.0, central_latitude=50.0)


def radial_psd(field: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (wavelength in km, power) of a square 2-D field."""
    n = field.shape[0]
    win = np.hanning(n)
    f = (field - field.mean()) * np.outer(win, win)
    power = np.abs(np.fft.fftshift(np.fft.fft2(f))) ** 2 / n**4
    k = np.fft.fftshift(np.fft.fftfreq(n))  # cycles per grid cell
    kr = np.hypot(*np.meshgrid(k, k)) * n
    bins = np.arange(0.5, n // 2, 1.0)
    idx = np.digitize(kr.ravel(), bins)
    psd = np.bincount(idx, weights=power.ravel(), minlength=len(bins) + 1)[1 : len(bins)]
    kc = 0.5 * (bins[1:] + bins[:-1])
    return n * DX_KM / kc, psd


def run_spectra(run_id: str) -> dict:
    cfg = OmegaConf.create({"streams": {STREAM: {"channels": CHANNELS}}})
    reader = WeatherGenZarrReader(cfg, run_id, None)
    ax = np.arange(-HALF_WIDTH_KM, HALF_WIDTH_KM, DX_KM) * 1e3
    gx, gy = np.meshgrid(ax, ax)
    out = {c: {"pred": [], "target": []} for c in CHANNELS}
    for sample in sorted(reader.get_samples()):
        data = reader.get_data(STREAM, samples=[sample], fsteps=[1])
        pred, target = data.prediction[1], data.target[1]
        xy = PROJ.transform_points(ccrs.PlateCarree(), pred.lon.values, pred.lat.values)[:, :2]
        vals = np.concatenate(
            [pred.sel(channel=CHANNELS).values[..., 0], target.sel(channel=CHANNELS).values.reshape(len(target.ipoint), len(CHANNELS))],
            axis=1,
        )
        grid = LinearNDInterpolator(xy, vals)(gx, gy)
        assert not np.isnan(grid).any(), "box extends outside the data domain"
        for i, c in enumerate(CHANNELS):
            wl, p = radial_psd(grid[..., i])
            _, t = radial_psd(grid[..., len(CHANNELS) + i])
            out[c]["pred"].append(p)
            out[c]["target"].append(t)
    return {"wavelength": wl, **{c: {k: np.mean(v, axis=0) for k, v in d.items()} for c, d in out.items()}}


def main():
    out_png = sys.argv[1]
    runs = dict(a.split("=", 1) for a in sys.argv[2:])
    res = {r: run_spectra(r) for r in runs}
    fig, axes = plt.subplots(2, len(CHANNELS), figsize=(6.5 * len(CHANNELS), 8), sharex=True)
    for j, c in enumerate(CHANNELS):
        first = next(iter(res.values()))
        axes[0, j].loglog(first["wavelength"], first[c]["target"], "k", lw=2, label="CERRA target")
        for r, label in runs.items():
            wl = res[r]["wavelength"]
            axes[0, j].loglog(wl, res[r][c]["pred"], label=label)
            axes[1, j].semilogx(wl, res[r][c]["pred"] / res[r][c]["target"], label=label)
            for wlen in (1000, 300, 100, 50):
                i = np.argmin(np.abs(wl - wlen))
                print(f"{r} {c} ratio at {wl[i]:.0f} km: {res[r][c]['pred'][i] / res[r][c]['target'][i]:.2f}")
        axes[1, j].axhline(1.0, color="k", lw=1)
        axes[0, j].set_title(f"{c}: power spectrum")
        axes[1, j].set_title(f"{c}: prediction / target power")
        axes[1, j].set_xlabel("wavelength [km]")
        axes[1, j].set_ylim(0, 1.3)
        for a in axes[:, j]:
            a.axvspan(2 * DX_KM, 50, color="0.9")
            a.grid(True, which="both", alpha=0.3)
            a.invert_xaxis()
    axes[0, 0].set_ylabel("power")
    axes[1, 0].set_ylabel("ratio")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("CERRA +3h forecast, mean of 8 samples from 2023-10-01 (grey: affected by interpolation)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)


if __name__ == "__main__":
    main()
