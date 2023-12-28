from ...utils import pretty_print
from ...utils.write_complete import write_complete
from celery import Task
from celery.utils.log import get_task_logger

import os

class PipelineTask(Task):
    """ 
    Define a custom task class for any logging or other universal 
    task functionality that needs to be handled. 

    Docs: https://docs.celeryq.dev/en/latest/userguide/tasks.html#handlers 
    """
    _logger = None

    @property
    def logger(self):
        """ Cached logger instance """
        if self._logger is None:
            self._logger = get_task_logger('pipeline')
        return self._logger    


    def before_start(self, task_id, args, kwargs):
        """ Run by the worker before the task starts executing """
        try: self.logger.debug(f'Starting task={self.name}: {pretty_print(args)}')
        except: self.logger.debug(f'Starting task={self.name}: {args}')
        super().before_start(task_id, args, kwargs)


    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """ Handler called after the task returns """
        try: self.logger.debug(f'Finished task={self.name}: {pretty_print(retval)}')
        except: self.logger.debug(f'Finished task={self.name}: {retval}')            
        super().after_return(status, retval, task_id, args, kwargs, einfo)


    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """ This is run by the worker when the task fails """
        #Write failure to specific log file
        from pathlib import Path
        if 'scene_id' in args[0].keys():
            out_string = task_id + '\n' + args[0]['scene_id'] + '\n' + str(einfo) + '\n' + "-------------------------------------------------\n"
        else:
            out_string = task_id + '\n' + '\n' + str(einfo) + '\n' + "-------------------------------------------------\n"
        with open( str(Path(__file__).resolve().parent.parent.parent.joinpath('Logs').joinpath('errors.txt')),"a") as error_file:
            error_file.write(out_string)
        
        #Write finished state 
        scene_path = args[0]['scene_path'] if 'scene_path' in args[0].keys() else 'no scene path defined' #args[0]['scene_path'] 
        #print(kwargs)
        ac_method  = kwargs['ac_method'] if 'ac_method' in kwargs.keys() else 'download'
        ac_methods = kwargs['global_config'].ac_methods
        
        write_complete(scene_path,ac_method,ac_methods,out_string,kwargs['global_config'].remove_scene_folder)
        super().on_failure(exc, task_id, args, kwargs, einfo)


    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """ This is run by the worker when the task is to be retried """
        super().on_retry(exc, task_id, args, kwargs, einfo)


    def on_success(self, retval, task_id, args, kwargs):
        """ Run by the worker if the task executes successfully """
        super().on_success(retval, task_id, args, kwargs)
