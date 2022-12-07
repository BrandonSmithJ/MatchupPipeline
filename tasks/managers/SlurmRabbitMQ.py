from ... import app
from .Worker import Worker

from pathlib import Path
from threading import Timer
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
        name   = Path(self.pkwargs.get('logfile', 'jobname')).stem
        outdir = Path(self.pkwargs.get('logfile', root.joinpath('Logs', '_'))).parent
        kwargs = {
            'job-name'    : name,
            'output'      : outdir.joinpath(f'{name}_out.txt').as_posix(),
            'error'       : outdir.joinpath(f'{name}_err.txt').as_posix(),
            'mem-per-cpu' : '4000',
            'time'        : '600:00',
            'account'     : 's2390',
        }
        kwargs  = [f'--{k}={v}' for k, v in kwargs.items()]
        command = ['srun'] + kwargs + [script] + command 
        return subprocess.Popen(command, **process_config)
