from .Worker import Worker

from pathlib import Path
import time, os


class SlurmProcess:
    """ Emulate the functionality of subprocess.Popen process """
    _ids = []
    

    def __init__(self, command, logdir='Logs/Slurm'):
        self.command = command
        self.logdir  = Path(logdir)

        script = Path(__file__).parent.joinpath('slurm_deploy.sh').as_posix()
        job_id = self.job_id = len(SlurmProcess._ids)
        SlurmWorker._ids.append(job_id)
        os.system(f'{script} {job_id} {command}')


    @property
    def stdout(self):
        """ File handle to the output log of the slurm job """
        return self.logdir.joinpath("{self.job_id}_out.txt").open('a+')


    @property
    def stderr(self):
        """ File handle to the error log of the slurm job """
        return self.logdir.joinpath("{self.job_id}_err.txt").open('a+')


    def poll(self):
        """ Get status of the slurm job """
	raise NotImplemented() # Return None unless the job is finished

    
    def communicate(self, timeout=None):
        """ Block execution until the slurm job completes """
        while self.poll() is None:
            time.sleep(2)


    def terminate(self):
        """ Force the job to terminate """
        raise NotImplemented() # Send termination signal via srun (?)



class SlurmWorker(Worker):
    """
    Rather than spawning a subprocess directly, the SlurmWorker
    class creates a Slurm job to spawn a new worker process. It
    then handles monitoring, restarting, and stopping this job
    as necessary.
    """

    def _spawn_process(self, command, **process_config):
        """ Spawn a new slurm job process """
        # Need to also spawn a thread timer to restart the slurm 
        # process occasionally due to max job times
        return SlurmProcess(command)


    def _start_new_process(self):
        """ Start a new slurm job """
        # 1. send signal to job to gracefully exit
        pass

        # 2. wait some (reasonable) period of time
        pass

        # 3. forcefully terminate if it hasn't yet 
        if self.process.poll() is None: self._kill_process()

        # 4. start a new process
        self._start_process()        
