from ... import app
#from ...__main__.py import app

from .Worker import Worker

from pathlib import Path
from threading import Timer
import subprocess, time, os

# Maximum runtime of a slurm job (in seconds) 
MAX_JOB_TIME = 0.5#60 * 60 * 1 


class SlurmProcess:
    """ Emulate the functionality of subprocess.Popen process """
    _ids = {}
    

    def __init__(self, command, pkwargs, logdir='pipeline/Logs/Slurm'):
        self.command = command
        self.logdir  = Path(logdir)
        self.pkwargs = pkwargs
        #job_name = self.job_name = f'MatchupPipeline-{len(SlurmProcess._ids)}'
        
        job_name = self.job_name = f'matchup_deployment_SLURM-{len(SlurmProcess._ids)}'
        job_id   = self.job_id   = self._execute(command)
        SlurmProcess._ids[job_id] = command # this is celery command
        print('Job ID:',job_id)
        print(command)


    def _execute(self, command):
        """ Execute the given command and parse the job ID """
        script = Path(__file__).parent.parent.parent.joinpath('scripts', 'slurm_deploy.sh').as_posix()
        print(['sbatch', script, self.job_name])
        output = subprocess.check_output(['sbatch', script, self.job_name] + command)
        assert(b'Submitted batch job' in output), output
        print('Submitted batch job: ',output)
        
        return output.decode('utf-8').strip().split(' ')[-1]


    @property
    def stdout(self):
        """ File handle to the output log of the slurm job """
        return self.logdir.joinpath(f"{self.job_id}_out.txt").open('a+')


    @property
    def stderr(self):
        """ File handle to the error log of the slurm job """
        return self.logdir.joinpath(f"{self.job_id}_err.txt").open('a+')


    def poll(self):
        """ Check if the slurm job is finished """
        cmd   = f'squeue -j {self.job_id} -h -o %T'
        state = subprocess.check_output(cmd.split())
        return None if state in ['PENDING', 'RUNNING'] else state


    def stop(self):
        """ Attempt to gracefully stop the job """ 
        return app.control.broadcast('shutdown', destination=[self.pkwargs['logname']])


    def terminate(self):
        """ Force the job to terminate """
        return subprocess.check_output(['scancel', self.job_id])


    def communicate(self, timeout=None):
        """ Block execution until the slurm job completes """
        if timeout is not None:
            def timed_out(): raise TimeoutError(f'{self} failed to gracefully stop')
            timer = Timer(timeout, timed_out)
    
        # Start the timeout thread and wait for process to complete (or timeout)
        try:
            if timeout is not None: 
                timer.start()

            while poll() is None:
                time.sleep(5)

        finally: 
            if timeout is not None:
                timer.cancel()
            


class SlurmWorker(Worker):
    """
    Rather than spawning a subprocess directly, the SlurmWorker
    class creates a Slurm job to spawn a new worker process. It
    then handles monitoring, restarting, and stopping this job
    as necessary.
    """
    def __init__(self, *args, slurm_kwargs={}, **kwargs):
        self.slurm_kwargs = slurm_kwargs
        super().__init__(*args, **kwargs)
        
        #print(self.pkwargs)

    def _spawn_process(self, command, **process_config):
        """ Spawn a new slurm job process """
        # Start a thread timer to restart the slurm 
        # process occasionally due to max job times
        # self.restart_timer = Timer(MAX_JOB_TIME, self._start_new_process)
        # self.restart_timer.start()
        # return SlurmProcess(command, self.pkwargs)
        root   = Path(__file__).parent.parent.parent
        script = root.joinpath('scripts', 'slurm_deploy2.sh').as_posix()
        name   = Path(self.pkwargs.get('logfile', 'jobname')).stem
        outdir = Path(self.pkwargs.get('logfile', root.joinpath('Logs', '_'))).parent
        kwargs = {
            'job-name'    : name,
            'output'      : outdir.joinpath(f'{name}_out.txt').as_posix(),
            'error'       : outdir.joinpath(f'{name}_err.txt').as_posix(),
            #'mem-per-cpu' : '4000',
            'time'        : '3:00:00',
            #'account'     : 's2390',
            'cpus-per-task' : 2
        }
        kwargs.update(self.slurm_kwargs)
        kwargs  = [f'--{k}={v}' for k, v in kwargs.items()]
        command = ['srun'] + kwargs + [script] + command 
        
        return subprocess.Popen(command, **process_config)

    def _stop_process2(self):
        """ Ensure we stop the job restart timer """
        if hasattr(self, 'restart_timer'):
            self.restart_timer.cancel()
        return super()._stop_process()
        

    def _start_new_process2(self):
        """ Start a new slurm job """
        # 1. send signal to job to gracefully exit
        self.process.stop()

        # 2. wait some (reasonable) period of time
        #self.communicate(timeout=60 * 5) # 5 minutes
        SlurmProcess.communicate(self, timeout=60 * 5) # 5 minutes
        
        # 3. forcefully terminate if it hasn't yet 
        if self.process.poll() is None: self._kill_process()

        # 4. start a new process
        self._start_process()        
