from ... import app
from .RabbitMQ import RabbitMQ

from pathlib import Path
from threading import Timer
from functools import lru_cache
import subprocess, time, os


class SlurmRabbitMQ(RabbitMQ):
    def _spawn_process(self, command, **process_config):
        """ Spawn a new slurm job process """
        # Start a thread timer to restart the slurm 
        # process occasionally due to max job times
        #self.restart_timer = Timer(MAX_JOB_TIME, self._start_new_process)
        #self.restart_timer.start()
        #return SlurmProcess(command)
        root   = Path(__file__).parent.parent.parent
        script = root.joinpath('scripts', 'slurm_deploy2.sh').as_posix()
        name   = Path(getattr(self, 'logfile', 'jobname')).stem
        outdir = Path(getattr(self, 'logfile', root.joinpath('Logs', '_'))).parent
        kwargs = {
            'job-name'    : name,
            'output'      : outdir.joinpath(f'{name}_out.txt').as_posix(),
            'error'       : outdir.joinpath(f'{name}_err.txt').as_posix(),
            #'mem-per-cpu' : '4000',
            'time'        : '120:00',
            'account'     : 's2390',
        }
        kwargs  = [f'--{k}={v}' for k, v in kwargs.items()]
        command = ['srun'] + kwargs + [script] + command 
        print(f'Spawning process with command: {command}')
        process = subprocess.Popen(command, **process_config)
        time.sleep(5)
 
        self.job_name = name
        self.job_id 
        return process


    @property
    @lru_cache()
    def job_id(self):
        jobs = self.get_output(f'sacct -u {self.username} --name {self.job_name}')
        return jobs.split('\n')[-1].split()[0].split('.')[0]


    @property
    def job_status(self): 
        status = self.get_output(f'squeue -j {self.job_id} -h -o %T')
        if 'Invalid job id' in status: raise Exception(f'Could get job id for {self.job_name}')
        return status 


    @property
    @lru_cache()
    def node(self):
        while self.job_status == 'PENDING': time.sleep(5)
        assert(self.job_status == 'RUNNING'), f'Bad status for {self.job_name}: {self.job_status}'
        self.host = '@' + self.get_output(f'squeue -j {self.job_id} -h -o %N')
        return self.host
