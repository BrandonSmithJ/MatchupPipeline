from ... import app, utils
from ..shutdown import shutdown
from .Process import Process 

from pathlib import Path 
from typing import Optional 
from functools import lru_cache
import subprocess, time, sys, os



class RabbitMQ(Process):
    """ RabbitMQ process """
    node = ''
    host = '@localhost'

    def __init__(self,
        logdir      : Path = Path('Logs'),  # Location to store log files 
        timeout     : Optional[int] = None, # Seconds to wait for graceful exit
        **kwargs,                           # Any additional command line keywords
    ):
        self.logfile = self._init_log(logdir, 'rabbitmq', kwargs)
        kwargs.update({
            'timeout' : timeout,
            #'action'  : f'> {self.logfile}',
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
            try: 
                self.get_status()
                return True
            except Exception as e: 
                #print(e)
                return False

        # Start the worker process
        super()._start_process()

        try: 
            print(f'Waiting for RabbitMQ to come online...', end='')
            sys.stdout.flush()
            while not check_running(): time.sleep(5)
            print('done')

        except (KeyboardInterrupt, Exception) as e: 
            self._kill_process()
            message = f'Exception starting RabbitMQ: {e}\n'
            message+= f'Worker kwargs: {utils.pretty_print(self.pkwargs)}'
            raise Exception(message)

        # Initialize user 
        for command in [self.add_vhost, self.add_user, self.set_tags, self.set_permissions]:
            try: 
                command()
                time.sleep(2)
            except Exception as e: 
                pass #print(f'Failed to run {command}: {e}')

        # Setup Celery app config
        address = f'{self.username}:mp{self.username}{self.host}'
        app.conf.broker_url=app.conf['broker_url'].replace('localhost', address)+f'/matchups_{self.username}'
        os.environ['CELERY_BROKER_URL'] = app.conf.broker_url        


    def _init_base_command(self):
        """ Find the RabbitMQ installation """
        rmq_path = next( Path('RabbitMQ').glob('rabbitmq_server-*') )
        bin_path = rmq_path.joinpath('sbin')
        assert(bin_path.exists()), f'Could not find RabbitMQ installation at "{bin_path}"'

        self.base_command = bin_path.joinpath('rabbitmq-server').as_posix()
        self.ctl_path     = bin_path.joinpath('rabbitmqctl').as_posix()


    def get_output(self, command):
        """ Get the output of a command """
        return subprocess.check_output(command.split(), stderr=subprocess.STDOUT).decode('utf-8').strip()


    def check_ctl(self, command):
        """ Get the output of a command for rabbitmqctl """
        return self.get_output(f'{self.ctl_path} --node rabbit{self.node} {command}')


    @property
    @lru_cache()
    def username(self):
        return self.get_output('whoami')    
    

    def get_status(self):
        return self.check_ctl('status')


    def add_vhost(self):
        return self.check_ctl(f'add_vhost matchups_{self.username}')


    def add_user(self):
        return self.check_ctl(f'add_user {self.username} mp{self.username}')

    def set_tags(self):
        return self.check_ctl(f'set_user_tags {self.username} administrator')

    def set_permissions(self):
        return self.check_ctl(f'set_permissions -p matchups_{self.username} {self.username} .* .* .*')


    def stop(self):
        return self.check_ctl('stop')



