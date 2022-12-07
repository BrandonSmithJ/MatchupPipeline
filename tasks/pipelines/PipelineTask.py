from ...utils import pretty_print

from celery import Task
from celery.utils.log import get_task_logger


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
        self.logger.debug(f'Starting task={self.name}: {pretty_print(args)}')
        super().before_start(task_id, args, kwargs)


    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """ Handler called after the task returns """
        self.logger.debug(f'Finished task={self.name}: {pretty_print(retval)}')
        super().after_return(status, retval, task_id, args, kwargs, einfo)


    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """ This is run by the worker when the task fails """
        super().on_failure(exc, task_id, args, kwargs, einfo)


    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """ This is run by the worker when the task is to be retried """
        super().on_retry(exc, task_id, args, kwargs, einfo)


    def on_success(self, retval, task_id, args, kwargs):
        """ Run by the worker if the task executes successfully """
        super().on_success(retval, task_id, args, kwargs)