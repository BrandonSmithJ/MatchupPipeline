#!/bin/bash

JOB_NAME=$1
COMMAND="${@:2}"

srun <<-EOT
	#!/bin/bash
	#SBATCH --job-name=$JOB_NAME
	#SBATCH --output=/discover/nobackup/bsmith16/Matchups2/pipeline/Logs/Out/$JOB_NAME.txt
	#SBATCH --error=Logs/Error/$JOB_NAME.txt
	#SBATCH --mem-per-cpu=4000
	#SBATCH --time=40:00
	#SBATCH --account=s2390
	
	echo "Job name: $JOB_NAME"
	echo "Command: $COMMAND"
        
        # source venv/bin/activate
        
        $COMMAND	
	success=\$?

	if [ \$success -ne 0 ]; then
		echo "Error code: \${success}"
	fi
EOT
