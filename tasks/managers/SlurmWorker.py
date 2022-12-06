from ... import app
from .Worker import Worker

from pathlib import Path
from threading import Timer
import subprocess, time, os

# Maximum runtime of a slurm job (in seconds) 
MAX_JOB_TIME = 60 * 60 * 1 


class SlurmProcess:
    """ Emulate the functionality of subprocess.Popen process """
    _ids = {}
    

    def __init__(self, command, logdir='Logs/Slurm'):
        self.command = command
        self.logdir  = Path(logdir)

        script   = Path(__file__).parent.joinpath('slurm_deploy.sh').as_posix()
        job_name = self.job_name = f'MatchupPipeline-{len(SlurmProcess._ids)}'
        job_id   = self.job_id   = subprocess.check_output([script, job_name, command])
        SlurmWorker._ids[job_id] = command


    @property
    def stdout(self):
        """ File handle to the output log of the slurm job """
        return self.logdir.joinpath("{self.job_id}_out.txt").open('a+')


    @property
    def stderr(self):
        """ File handle to the error log of the slurm job """
        return self.logdir.joinpath("{self.job_id}_err.txt").open('a+')


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

            while self.poll() is None:
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

    def _spawn_process(self, command, **process_config):
        """ Spawn a new slurm job process """
        # Start a thread timer to restart the slurm 
        # process occasionally due to max job times
        self.restart_timer = Timer(MAX_JOB_TIME, self._start_new_process)
        self.restart_timer.start()
        return SlurmProcess(command)


    def _stop_process(self):
        """ Ensure we stop the job restart timer """
        if hasattr(self, 'restart_timer'):
            self.restart_timer.cancel()
        return super()._stop_process()
        

    def _start_new_process(self):
        """ Start a new slurm job """
        # 1. send signal to job to gracefully exit
        self.process.stop()

        # 2. wait some (reasonable) period of time
        self.communicate(timeout=60 * 5) # 5 minutes

        # 3. forcefully terminate if it hasn't yet 
        if self.process.poll() is None: self._kill_process()

        # 4. start a new process
        self._start_process()        
