from ... import app, utils
from ..shutdown import shutdown
from .Process import Process 

from pathlib import Path 
from typing import Optional 
from functools import lru_cache
import time, sys



class RabbitMQ(Process):
    """ RabbitMQ process """

    def __init__(self,
        logdir      : Path = Path('Logs'),  # Location to store log files 
        timeout     : Optional[int] = None, # Seconds to wait for graceful exit
        **kwargs,                           # Any additional command line keywords
    ):
        self.logfile = self._init_log(logdir, 'rabbitmq', kwargs)
        kwargs.update({
            'timeout' : timeout,
            'action'  : f'> {self.logfile}',
        })
        self._init_base_command()
        super().__init__(**kwargs)


    def _stop_process(self):
        """ Stop background process """
        if self.process is None: return 

        # Send shutdown signal if this process is still active
        if self.process.poll() is None: self.stop()

        # Attempt to gracefully stop RabbitMQ
        try:
            self.process.communicate(timeout=self.timeout)
            self.process = None

        # Force kills if we weren't able to gracefully exit
        finally: super()._stop_process()



    def _start_process(self):
        """ Start the required process in the background """
            
        def check_running():
            try: return self.get_status()
            except: return False

        # Start the worker process
        super()._start_process()

        try: 
            if not check_running():
                print(f'Waiting for RabbitMQ to come online...', end='')
                sys.stdout.flush()
                while not check_running(): time.sleep(1)
                print('done')

        except (KeyboardInterrupt, Exception) as e: 
            self._kill_process()
            message = f'Exception starting RabbitMQ: {e}\n'
            message+= f'Worker kwargs: {utils.pretty_print(self.pkwargs)}'
            raise Exception(message)

        # Initialize user 
        for command in [self.add_vhost, self.add_user]:
            try: command()
            except: pass



    def _init_base_command(self):
        """ Find the RabbitMQ installation """
        rmq_path = next( Path('RabbitMQ').glob('rabbitmq_server-*') )
        bin_path = rmq_path.joinpath('sbin')
        assert(bin_path.exists()), f'Could not find RabbitMQ installation at "{bin_path}"'

        self.base_command = bin_path.joinpath('rabbitmq-server').as_posix()
        self.ctl_path     = bin_path.joinpath('rabbitmqctl').as_posix()


    def get_output(self, command):
        """ Get the output of a command """
        return subprocess.check_output(command.split())


    @property
    @lru_cache()
    def username(self):
        return self.get_output('whoami')    
    

    def get_status(self):
        return self.get_output(f'{self.ctl_path} status')


    def add_vhost(self):
        return self.get_output(f'{self.ctl_path} add_vhost matchups_{self.username}')


    def add_user(self):
        return [
            self.get_output(f'{self.ctl_path} add_user {self.username} mp{self.username}'),
            self.get_output(f'{self.ctl_path} set_user_tags {self.username} administrator'),
            self.get_output(f'{self.ctl_path} set_permissions -p / {self.username} ".*" ".*" ".*"'),
        ]


    def stop(self):
        return self.get_output(f'{self.ctl_path} stop')



