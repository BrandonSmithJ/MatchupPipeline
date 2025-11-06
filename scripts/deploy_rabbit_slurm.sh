#!/bin/bash
#SBATCH --job-name=rabbit_deploy
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --time=03:00:00
#SBATCH --partition=ubuntu20
#SBATCH --exclude=slrm[0001-0054]
#SBATCH --output=out/%x-%j.out
#SBATCH --error=err/%x-%j.err
source /tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/.bash_aliases
activateMatchupEnv
cd pipeline/scripts/
relaunch_rabbit.sh
