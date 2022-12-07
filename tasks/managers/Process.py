from ...utils import pretty_print

from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from pathlib import Path 
from typing import Optional
import subprocess, time




class Process:
    """ Context manager for background processes """
    base_command = 'celery -A pipeline'


    def __init__(self,
        timeout : Optional[int] = None, # Seconds to wait for graceful exit
        **kwargs,                       # Command line arguments for process
    ):
        self.process = None
        self.monitor = None
        self.timeout = timeout
        self.pkwargs = kwargs

    # Check if process has been started
    def running(self): return self.process is not None

    # Alternative to context manager __exit__
    def close(self):   return self._stop_process()

    # Context managers
    def __enter__(self, *args, **kwargs): return self._start_process()
    def  __exit__(self, *args, **kwargs): return self._stop_process()

    # Iterate over lines from stdout/stderr of the process
    def  __iter__(self): return self._read_process()



    # ================================================================
    # Private functions

    def _init_log(self, 
        logdir   : str,                   # Directory log will be written to 
        filename : str,                   # Log filename (minus extension)
        kwargs   : Optional[dict] = None, # Kwargs written to top of file
    ) -> str:                             # Return string path of the file
        """ Create log directory if necessary, and clear prior log file """
        root = Path(__file__).parent.parent.parent.joinpath(logdir)
        path = root.joinpath(f'{filename}.log')
        root.mkdir(exist_ok=True, parents=True)
        path.write_text( pretty_print(kwargs or '') + '\n')
        return path.as_posix()



    def _spawn_process(self, command, **process_config):
        """ Create a process object which executes the given command """
        return subprocess.Popen(command, **process_config)



    def _start_process(self):
        """ Start the required process in the background """

        def execute(action='', **kwargs):
            """ Execute celery action in a separate process """
            process_config = {
                'stdout' : subprocess.PIPE, 
                'stderr' : subprocess.STDOUT,
                'text'   : True,
            }
            kwargs  = ' '.join( f'--{k}={v}' for k,v in kwargs.items() )
            command = f'{self.base_command} {action} {kwargs}'.split()
            return self._spawn_process(command, **process_config)

        self.process = self.process or execute(**self.pkwargs)
        return self



    def _stop_process(self):
        """ Stop background process """
        # Inheriting class should implement _stop_process to gracefully stop 
        self._kill_process()

        # Clear monitor queue so threads can exit
        list(self.monitor or [])
        self.monitor = None



    def _kill_process(self):
        """ Force kill the worker process """
        if self.process is not None:
            getattr(self.process, 'kill', self.process.terminate)()
            self.process = None



    @staticmethod
    def _enqueue(file, queue):
        """ Helper to put text in the queue """
        for line in iter(file.readline, ''):
            queue.put(line)



    def _read_process(self):
        """ Read stdout/stderr for the worker process """
        sentinel = '<SENTINEL VALUE>'

        def monitor(process):
            """ Read process from a separate thread to prevent blocking """
            with ThreadPoolExecutor(1) as executor:
                queue = Queue()
                executor.submit(Process._enqueue, process.stdout, queue)

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

        if self.process is None: return
        if self.monitor is None: self.monitor = monitor(self.process)
        return iterate_until_empty(self.monitor)
