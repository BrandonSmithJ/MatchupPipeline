from .Process import Process 

from pathlib import Path 
from typing import Optional 



class Flower(Process):
    """ Flower process (Celery job monitor) """

    def __init__(self,
        logdir      : Path = Path('Logs'),  # Location to store log files 
        timeout     : Optional[int] = None, # Seconds to wait for graceful exit
        **kwargs,                           # Any additional command line keywords
    ):
        kwargs.update({
            'timeout'    : timeout,
            'action'     : 'flower',
            'broker_api' : 'http://guest:guest@localhost:15672/api/',            
        })
        kwargs['log_file_prefix'] = self._init_log(logdir, 'flower', kwargs)
        super().__init__(**kwargs)