#!/bin/bash
username="$(whoami)"
echo User is: $username

echo Copying main script...
cp -n /home/roshea/matchup_pipeline_development/main_default.py ./main.py

#Make Ancillary directories for Polymer
mkdir ANCILLARY
chmod 777 ANCILLARY
chmod g+s ANCILLARY
setfacl -d -m g::rwx ./ANCILLARY/
setfacl -d -m o::rwx ./ANCILLARY/
setfacl -R -m g::rwx ./ANCILLARY/
setfacl -R -m o::rwx ./ANCILLARY/

mkdir ANCILLARY/METEO 

if [ ! -d pipeline ]; then
	echo Clonning repo...
	git clone https://github.com/BrandonSmithJ/MatchupPipeline.git pipeline
fi

echo Switching to image processing pipeline branch...

cd pipeline

git checkout image_processing_pipeline
git config core.fileMode false

chmod 777 -R ../pipeline

#chmod -R 777 AC
chmod g+s ../pipeline
setfacl -d -m g::rwx ../pipeline
setfacl -d -m o::rwx ../pipeline
setfacl -R -m g::rwx ../pipeline
setfacl -R -m o::rwx ../pipeline

echo Copying non-git elements, MDN...
cp -nr /home/roshea/matchup_pipeline_development/pipeline/MDNs/ ./

echo Copying credentials...
cp -nr /home/roshea/matchup_pipeline_development/pipeline/credentials/ ./
cp -nr /home/roshea/matchup_pipeline_development/pipeline/credentials/roshea ./credentials/$username
cp -nr /home/roshea/matchup_pipeline_development/pipeline/API/sources/gsutil/ ./API/sources/


echo Copying default configuration...
cp -nr ./configs/default.py ./configs/$username.py

echo Setting up Insitu test data...
mkdir /data/$username/SCRATCH
mkdir /data/$username/SCRATCH/Insitu

echo Copying insitu test data...
cp -nr /data/roshea/SCRATCH/Insitu/OLI_test_image    /data/$username/SCRATCH/Insitu/
cp -nr /data/roshea/SCRATCH/Insitu/MSI_test_image_CB /data/$username/SCRATCH/Insitu/
cp -nr /data/roshea/SCRATCH/Insitu/OLCI_test_image   /data/$username/SCRATCH/Insitu/

echo Copying Google credentials
cp -n /home/roshea/.boto ~/.boto

echo __________________________________________________________________________________________________________________
echo Complete! To test installation on OLI imagery run main script with environment active...

echo 1. source /data/roshea/matchup_pipeline_env/bin/activate

echo 2. python main.py

echo 3. After successful test: Update credentials within pipeline/credentials/{username} also update the ~/.boto file at home directory
