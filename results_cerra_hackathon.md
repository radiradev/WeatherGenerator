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
