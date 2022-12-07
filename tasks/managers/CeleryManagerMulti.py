from ... import app, utils, NCCS
from ..shutdown import shutdown

from .Worker  import Worker
from .Flower  import Flower
from .Monitor import Monitor


# Switch to the SLURM worker if we're running on NCCS
if NCCS: 
    from .SlurmWorker import SlurmWorker as Worker
    from .SlurmRabbitMQ import SlurmRabbitMQ as RabbitMQ


class CeleryManagerMulti:
    """ 
    Context manager which handles creation / cleanup of background processes
    necessary for running Celery and Flower:

        worker_kws = [
            # Multiple threads for parallelism
            {   'logname'     : 'worker1',
                'queues'      : ['celery'], 
                'concurrency' : 10, 
            },

            # Single dedicated thread (e.g. for writing) 
            {   'logname'     : 'worker2',
                'queues'      : ['dedicated'], 
                'concurrency' : 1, 
            },
        ]

        with CeleryManagerMulti(worker_kws) as manager:
            print(f'Running: {manager.running()}')

            # Read stdout/stderr from respective processes
            for line in manager.read_celery(): print(line)
            for line in manager.read_flower(): print(line)

    """

    def __init__(self, 
        worker_kws : list = [{}], # List of kwarg dicts for workers
        data       : list = [],   # Data samples
        ac_methods : list = [],   # AC methods
        **kwargs,                 # Any other kwargs to pass Worker/Flower
    ):
        self.rabbit  = [RabbitMQ()]

        utils.purge_queues()
        merge_kwargs = lambda d: (d.update(kwargs) or d)
        self.celery  = [Worker(**merge_kwargs(kw)) for kw in worker_kws]
        self.flower  = [Flower()]
        self.monitor = [Monitor(data, ac_methods)]


    # Context managers
    def __enter__(self, *args, **kwargs): return self._start_processes()
    def  __exit__(self, *args, **kwargs): return self._stop_processes()

    # Iterate over all processes
    def __iter__(self): yield from self._iter_processes()

    # Iterate over lines from stdout/stderr of the respective process
    def read_celery(self): return self._read_process('celery')
    def read_flower(self): return self._read_process('flower')
    def read_rabbit(self): return self._read_process('rabbit')

    # Check if processes have been started
    def running(self): return any(proc.running() for proc in self)

    # Alternative to context manager __exit__
    def close(self):   return self._stop_processes()



    # ================================================================
    # Private functions

    def _start_processes(self):
        """ Start the required processes in the background """
        [process._start_process() for process in self]
        return self



    def _stop_processes(self):
        """ Stop all background processes """
        for i, process in enumerate(self):
            try:     process.close()
            except:  print(f'Encountered error, killing process {i}')
            finally: process._kill_process()



    def _kill_processes(self):
        """ Force kill all background processes """
        for process in self:
            process._kill_process()



    def _iter_processes(self):
        """ Iterate over processes """
        for name in ['celery', 'flower', 'monitor', 'rabbit']:
            yield from getattr(self, name, [])



    def _read_process(self, name: str):
        """ Read stdout/stderr for the requested process(es) """
        for process in getattr(self, name, []):
            yield from process
