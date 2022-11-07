from ... import app, utils
from ..shutdown import shutdown
from .Process import Process 

from pathlib import Path 
from typing import Optional 
import time, sys



class Worker(Process):
    """ Celery worker process """

    def __init__(self,
        concurrency : int  = 1,             # Number of threads for the worker
        queues      : list = ['celery'],    # List of queues to consume from
        logname     : str  = 'celery',      # Log file name
        logdir      : Path = Path('Logs'),  # Location to store log files 
        loglevel    : str  = 'INFO',        # Log level
        timeout     : Optional[int] = None, # Seconds to wait for graceful exit
        **kwargs,                           # Any additional command line keywords
    ):
        kwargs.update({
            'timeout'     : timeout,
            'action'      : 'worker',
            'loglevel'    : loglevel,
            'hostname'    : f'{logname}@%h',
            'queues'      : ','.join(map(str, queues)),
            'concurrency' : concurrency,
        })
        kwargs['logfile'] = self._init_log(logdir, logname, kwargs)
        super().__init__(**kwargs)



    def _start_process(self):
        """ Start the worker process in the background """

        def celery_running():
            """ Check if any celery workers are available """
            return app.control.inspect().ping() is not None

        def worker_running(hostname):
            if hostname is None: return True
            nodes = app.control.inspect().stats()
            strip = lambda name: name.split('@')[0]
            match = lambda node: strip(hostname) == strip(node)
            return any(map(match, nodes))

        def wait_for_online(label, running):
            if not running():
                print(f'Waiting for {label[:-3]} to come online...', end='')
                sys.stdout.flush()
                while not running(): time.sleep(1)
                print('done')

        # Start the worker process
        super()._start_process()

        # Wait for Celery and this worker to come online
        hostname = self.pkwargs.get('hostname', None)
        runners  = {
            'Celery app   '      : celery_running,
            f'Worker {hostname}' : lambda: worker_running(hostname),
        }

        for label, running in runners.items():
            try: wait_for_online(label, running)

            except (KeyboardInterrupt, Exception) as e: 
                self._kill_process()
                message = f'Exception starting Celery Worker: {e}\n'
                message+= f'Worker kwargs: {utils.pretty_print(self.pkwargs)}'
                raise Exception(message)
        return self



    def _stop_process(self):
        """ Stop background process """
        if self.process is None: return 

        # Send shutdown signal if this process is still active
        if self.process.poll() is None: shutdown.delay()

        # Attempt to gracefully stop Celery worker
        try:
            self.process.communicate(timeout=self.timeout)
            self.process = None

        # Force kills if we weren't able to gracefully exit
        finally: super()._stop_process()
