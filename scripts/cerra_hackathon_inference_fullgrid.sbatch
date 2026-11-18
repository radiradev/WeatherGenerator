#!/bin/bash
#SBATCH --job-name=cerra_infer
#SBATCH --partition=normal
#SBATCH -A wghack-course2026-cscs
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=16
#SBATCH --gpus=4
#SBATCH --mem=400G
#SBATCH --time=00:25:00
#SBATCH --output=/iopsstor/scratch/cscs/%u/inference_cerra/logs/%x.%j.out
#SBATCH --error=/iopsstor/scratch/cscs/%u/inference_cerra/logs/%x.%j.err

# Full-grid inference (4 validation samples from 2023-10-01, latest checkpoint, all
# 755,161 CERRA grid points written via max_num_targets=-1) for the four CERRA runs.
export LOGS=/iopsstor/scratch/cscs/$USER/inference_cerra/logs
uenv run prgenv-gnu/25.6:v2 --view=modules,default -- bash << 'EOS'
ulimit -c 0
export CC=/usr/bin/gcc
cd $HOME/WeatherGenerator
source .venv/bin/activate
run() {
  srun --exact --ntasks=1 --gpus=1 --cpus-per-task=16 --export=ALL python -u src/weathergen/run_train.py inference \
    --from-run-id $1 --run-id $2 \
    --options test_config.samples_per_mini_epoch=4 test_config.output.num_samples=4 streams.CERRA.max_num_targets=-1 \
              data_loading.num_workers=4 < /dev/null > $LOGS/$2.log 2>&1
  echo "$1 -> $2 exit $?"
}
date
run mxtynk0b mxtyinf1; run je43887w je43inf1; run rlufbwfc rlufinf1; run isk98cas isk9inf1
date
EOS
