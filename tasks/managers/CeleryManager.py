from ... import app
from ..shutdown import shutdown

from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from typing import Optional
from pathlib import Path
import subprocess, time



class CeleryManager:
    """ 
    Context manager which handles creation / cleanup of background processes
    necessary for running Celery and Flower:

        with CeleryManager() as manager:
            print(f'Running: {manager.running()}')

            # Read stdout/stderr from respective processes
            for line in manager.read_celery(): print(line)
            for line in manager.read_flower(): print(line)

    """
    monitors = {}  # Generators which read celery/flower stdouts/stderrs

    celery = None  # Celery subprocess.Popen object
    flower = None  # Flower subprocess.Popen object 

    celery_kws = { # Pass to Celery when starting the process
        'action'     : 'worker',
        'loglevel'   : 'INFO',
    } 

    flower_kws = { # Pass to Flower when the starting process
        'action'     : 'flower',
        'broker_api' : 'http://guest:guest@localhost:15672/api/',
    } 


    def __init__(self, 
        logdir  : str           = 'Logs', # Location to store log files 
        timeout : Optional[int] = None,   # Seconds to wait for graceful exit
    ):
        self.timeout = timeout
        self._init_logs(logdir)


    # Iterate over lines from stdout/stderr of the respective process
    def read_celery(self): return self._read_process('celery')
    def read_flower(self): return self._read_process('flower')

    # Check if processes have been started
    def running(self): return CeleryManager.celery is not None

    # Context managers
    def __enter__(self, *args, **kwargs): return self._start_processes()
    def  __exit__(self, *args, **kwargs): return self._stop_processes()



    # ================================================================
    # Private functions

    def _init_logs(self, logdir):
        """ Create the log files and clear any prior logs """
        root = Path(__file__).parent.parent.joinpath(logdir)
        root.mkdir(exist_ok=True, parents=True)

        for name, (kws, key) in {
            'celery' : (self.celery_kws, 'logfile'),
            'flower' : (self.flower_kws, 'log_file_prefix'),
        }.items():
            kws[key] = root.joinpath(f'{name}.txt').as_posix()
            Path(kws[key]).write_text('')



    def _start_processes(self):
        """ Start the required processes in the background """

        def execute(action, **kwargs):
            """ Execute celery action in a separate process """
            process_config = {
                'stdout' : subprocess.PIPE, 
                'stderr' : subprocess.STDOUT,
                'text'   : True,
            }
            kwargs  = ' '.join( f'--{k}={v}' for k,v in kwargs.items() )
            command = f'celery -A pipeline {action} {kwargs}'.split()
            return subprocess.Popen(command, **process_config)

        try:
            if not self.running():
                CeleryManager.celery = execute(**self.celery_kws)
                CeleryManager.flower = execute(**self.flower_kws)

            # Wait for celery to come online
            print('Waiting for Celery app to come online...', end='')
            while app.control.inspect().ping() is None: 
                print("No ping detected",self.running())
                #time.sleep(1)
            print('done')

        except:
            print(f'Exception starting Celery and Flower processes')
            self._kill_processes()
        return self



    def _stop_processes(self):
        """ Stop all background processes """
        if not self.running(): return 

        # Attempt to gracefully kill Celery
        shutdown.delay()

        try:
            CeleryManager.celery.communicate(timeout=self.timeout)
            CeleryManager.celery = None
        except: pass

        # Flower doesn't have a graceful kill method
        finally: self._kill_processes()

        # Need to first clear monitor queues so threads can exit
        [list(monitor) for monitor in CeleryManager.monitors.values()]
        CeleryManager.monitors.clear()



    def _kill_processes(self):
        """ Force kill all background processes """
        for name in ['celery', 'flower']:
            process = getattr(CeleryManager, name, None)

            if process is not None:
                getattr(process, 'kill', process.terminate)()
                setattr(CeleryManager, name, None)



    @staticmethod
    def _enqueue(file, queue):
        """ Helper to put text in the queue """
        for line in iter(file.readline, ''):
            queue.put(line)



    def _read_process(self, name):
        """ Read stdout for the given process """
        sentinel = '<SENTINEL VALUE>'

        def monitor(process):
            """ Read process from a separate thread to prevent blocking """
            with ThreadPoolExecutor(1) as executor:
                queue = Queue()
                executor.submit(CeleryManager._enqueue, process.stdout, queue)

                while (process.poll() is None) or not queue.empty():
                    output = sentinel
                    try:          output = queue.get_nowait().strip()
                    except Empty: pass
                    yield output

        def iterate_until_empty(generator, iters=10):
            """ Read multiple times to deal with Queue.empty unreliability """
            for _ in range(iters):
                time.sleep(0.2)

                while True:
                    output = next(generator)
                    if output == sentinel: break
                    yield output

        process = getattr(CeleryManager, name, None)
        if process is None: return

        if name not in CeleryManager.monitors:
            CeleryManager.monitors[name] = monitor(process)
        return iterate_until_empty(CeleryManager.monitors[name])
