# CERRA hackathon runs: interim results

Status on 18 Nov 2026, 19:00 CET. All six runs are unfinished: they were stopped
when the shared `wghack-course2026-cscs` account reached its node-hour limit.
Each run is configured for 64 mini-epochs of 4096 samples. Run definitions and
Slurm job ids are in `runs_cerra_hackathon.csv`.

Plots were made with `plot_train`; the numbers below are read from the same
training logs. Losses are MSE on normalised target channels, averaged over channels.
"FE" means the forecasting engine (16 blocks, trained from scratch).

## CERRA +3h forecast (targets `10si`, `r_850`)

| Run | Setup | Mini-epochs done | Samples at last validation | Validation MSE | `10si` | `r_850` |
|---|---|---|---|---|---|---|
| `mxtynk0b` | CERRA, no FE | 14 | 58,344 | 0.067 | 0.073 | 0.061 |
| `je43887w` | CERRA, FE | 12 | 50,152 | 0.105 | 0.112 | 0.098 |
| `rlufbwfc` | CERRA + ERA5 O96 input, no FE | 8 | 35,768 | 0.080 | 0.086 | 0.074 |
| `isk98cas` | CERRA + ERA5 O96 input, FE | 7 | 29,672 | 0.116 | 0.120 | 0.112 |

At a matched point of about 30,000 samples:

| Run | Samples | Validation MSE |
|---|---|---|
| `mxtynk0b` (CERRA, no FE) | 29,672 | 0.088 |
| `rlufbwfc` (CERRA + ERA5, no FE) | 31,672 | 0.083 |
| `isk98cas` (CERRA + ERA5, FE) | 29,672 | 0.116 |
| `je43887w` (CERRA, FE) | 29,672 | 0.137 |

![CERRA runs, training and validation loss](assets/cerra_hackathon/mxtynk0b_je43887w_rlufbwfc_isk98cas_train_val_fs_0_1_mse_CERRA_avg.png)

## ERA5 O96 only, +3h forecast (targets `10u`, `10v`, `q_850`)

| Run | Setup | Mini-epochs done | Samples at last validation | Validation MSE | `10u` | `10v` | `q_850` |
|---|---|---|---|---|---|---|---|
| `gjwg0n0v` | ERA5 only, no FE | 25 | 103,400 | 0.0085 | 0.0067 | 0.0098 | 0.0091 |
| `dwu8hmc7` | ERA5 only, FE | 17 | 69,536 | 0.0228 | 0.0192 | 0.0256 | 0.0237 |

At about 70,000 samples the run without the forecasting engine was at 0.0095
against 0.0228 with it.

![ERA5 runs, training and validation loss](assets/cerra_hackathon/gjwg0n0v_dwu8hmc7_train_val_fs_0_1_mse_ERA5_avg.png)

## What the curves show so far

- In all three pairs, the run with the forecasting engine has higher loss than
  the run without it at the same number of samples. The gap is narrowing slowly
  on CERRA and is roughly constant on ERA5.
- Adding ERA5 O96 as an extra input makes little difference without the
  forecasting engine (0.083 against 0.088 at about 30,000 samples). With the
  forecasting engine it helps more (0.116 against 0.137).
- Validation tracks training closely in every run, so there is no sign of
  overfitting yet.
- No run has flattened out. These are early numbers (11% to 39% of the planned
  training) and the ranking could still change.
- The CERRA and ERA5 losses are not comparable with each other: the target
  variables and grids differ.

## Throughput

| Run | Steps per second (4 GPUs) |
|---|---|
| `mxtynk0b` | 0.43 |
| `je43887w` | 0.35 |
| `rlufbwfc` | 0.33 |
| `isk98cas` | 0.29 |
| `gjwg0n0v` | 0.95 |
| `dwu8hmc7` | 0.66 |

## Reproducing the plots

```
plot_train -o plots/cerra_hackathon --legend-outside --streams CERRA \
  -fd "{'mxtynk0b': 'CERRA, no FE', 'je43887w': 'CERRA, FE', 'rlufbwfc': 'CERRA+ERA5 input, no FE', 'isk98cas': 'CERRA+ERA5 input, FE'}"
plot_train -o plots/cerra_hackathon --legend-outside --streams ERA5 \
  -fd "{'gjwg0n0v': 'ERA5 only, no FE', 'dwu8hmc7': 'ERA5 only, FE'}"
```

## Inference: scores, fields and spectra

Inference was run from the latest checkpoint of each run on 8 consecutive
3-hourly validation samples starting 2023-10-01 (+3h forecast, one step).
Eight samples from a single day is a small sample, and the checkpoints have
seen different amounts of training (7 to 25 mini-epochs, see above), so the
comparison between runs is indicative only.

The CERRA runs predict a random half of the grid points per sample
(`max_num_targets: 375000`). For the field plots and spectra below they were
run a second time on the first 4 samples with `max_num_targets=-1`, so that
all 755,161 points of the 869 x 869 grid are written. The scores table uses
the first set of runs (8 samples).

### Scores

RMSE in physical units from `evaluate`. CERRA scores are over the `europe`
region (35 to 70 N, 10 W to 40 E); ERA5 scores are global.

| Run | Setup | Mini-epochs | RMSE `10si` [m/s] | RMSE `r_850` [%] |
|---|---|---|---|---|
| `mxtynk0b` | CERRA, no FE | 14 | 0.94 | 6.8 |
| `je43887w` | CERRA, FE | 12 | 1.18 | 8.9 |
| `rlufbwfc` | CERRA + ERA5 input, no FE | 8 | 1.05 | 7.4 |
| `isk98cas` | CERRA + ERA5 input, FE | 7 | 1.21 | 9.5 |

| Run | Setup | Mini-epochs | RMSE `10u` [m/s] | RMSE `10v` [m/s] | RMSE `q_850` [g/kg] |
|---|---|---|---|---|---|
| `gjwg0n0v` | ERA5 only, no FE | 25 | 0.49 | 0.50 | 0.41 |
| `dwu8hmc7` | ERA5 only, FE | 17 | 0.82 | 0.83 | 0.70 |

### CERRA fields, valid 2023-10-01 06:00

Full grid in its native Lambert projection, sample 0. Top row: target and the
+3h prediction of each run. Bottom row: prediction minus target, with the RMSE
over the whole domain for this one sample.

10 m wind speed (`10si`):

![CERRA 10 m wind speed fields](assets/cerra_hackathon/cerra_fields_10si.jpg)

Relative humidity at 850 hPa (`r_850`):

![CERRA 850 hPa relative humidity fields](assets/cerra_hackathon/cerra_fields_r_850.jpg)

- All four predictions place the large-scale structures correctly but are
  visibly smoother than the target; fine structure over land and in the
  humidity filaments is missing.
- The two runs with the forecasting engine show blocky tile edges, most
  clearly in `r_850`. The runs without it show them only faintly.
- Errors are largest along fronts and in the cyclone in the north-west.

### ERA5 fields, 10 m zonal wind, valid 2023-10-01 06:00

| Target | No FE | FE |
|---|---|---|
| ![](assets/cerra_hackathon/map_era5_10u_target.jpg) | ![](assets/cerra_hackathon/map_era5_10u_pred_no_fe.jpg) | ![](assets/cerra_hackathon/map_era5_10u_pred_fe.jpg) |

### CERRA spectra

The built-in `psd` metric needs a global or regular lat-lon grid, so it does
not apply to CERRA. `scripts/cerra_hackathon_spectra.py` computes a radially
averaged 2-D FFT spectrum directly on the native 869 x 869 grid (5.4 km
spacing, mean removed, Hann window), averaged over the 4 full-grid samples.
No interpolation is involved.

| `10si` | `r_850` |
|---|---|
| ![CERRA 10si spectrum](assets/cerra_hackathon/cerra_spectrum_10si.png) | ![CERRA r_850 spectrum](assets/cerra_hackathon/cerra_spectrum_r_850.png) |

Ratio of predicted to target power:

| Run | `10si` 300 km | `10si` 100 km | `10si` 50 km | `r_850` 300 km | `r_850` 100 km | `r_850` 50 km |
|---|---|---|---|---|---|---|
| CERRA, no FE | 0.81 | 0.44 | 0.23 | 0.74 | 0.16 | 0.08 |
| CERRA, FE | 0.66 | 0.34 | 0.13 | 0.35 | 0.08 | 0.07 |
| CERRA + ERA5 input, no FE | 0.69 | 0.40 | 0.18 | 0.75 | 0.14 | 0.07 |
| CERRA + ERA5 input, FE | 0.66 | 0.30 | 0.13 | 0.34 | 0.11 | 0.10 |

- All four runs are too smooth. Power is about right at wavelengths above
  roughly 1,000 km and falls increasingly short at smaller scales.
- Humidity is blurred much more than wind: at 100 km the predictions keep 8%
  to 16% of the target power for `r_850` against 30% to 44% for `10si`.
- The runs with the forecasting engine lose power at larger scales than the
  runs without it, most clearly for `r_850` (about 0.35 against 0.75 at 300 km).
- Below about 15 km the `r_850` predictions have more power than the target
  (12 to 29 times more at 12 km). The target has almost no power at these
  scales, so this is a small amount of grid-scale noise in the predictions,
  largest in the runs with the forecasting engine. `10si` does not show it.

### ERA5 spectra

Spherical-harmonic spectra from `evaluate` (`psd`, method `sht`), 8 samples,
re-plotted so that both runs share one figure.

![ERA5 spectra](assets/cerra_hackathon/era5_spectra.png)

Ratio of predicted to target power:

| Run | `10u` wavenumber 50 | `10u` 90 | `10v` 50 | `10v` 90 | `q_850` 50 | `q_850` 90 |
|---|---|---|---|---|---|---|
| ERA5 only, no FE | 0.99 | 0.93 | 0.99 | 0.94 | 0.99 | 0.87 |
| ERA5 only, FE | 0.89 | 0.72 | 0.90 | 0.78 | 0.85 | 0.62 |

The run without the forecasting engine matches the target spectrum to within
a few percent up to wavenumber 50 and loses 6% to 13% at wavenumber 90. The run
with the forecasting engine loses 22% to 38% there. The ERA5 runs are much
closer to their target spectra than the CERRA runs, but they have also trained
for longer and the O96 grid has no scales below about 100 km to resolve.

### Reproducing

```
sbatch scripts/cerra_hackathon_inference.sbatch            # 8 samples, subsampled targets
sbatch scripts/cerra_hackathon_inference_fullgrid.sbatch   # 4 samples, full CERRA grid
evaluate --config config/evaluate/eval_cerra_hackathon_cerra.yml
evaluate --config config/evaluate/eval_cerra_hackathon_era5.yml
python scripts/cerra_hackathon_spectra.py <eval_dir> assets/cerra_hackathon
```

`<eval_dir>` is the directory the evaluation configs write to; the spectra
script reads the ERA5 `psd` scores from it and writes the field panels and
spectrum figures. The inference run ids are the training run id's first four
characters plus `inf0` (subsampled) or `inf1` (full grid). Output paths in the
job scripts and evaluation configs are specific to this cluster account.
