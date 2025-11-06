
def get_celery_worker_status():
    ERROR_KEY = "ERROR"
    try:
        from .. import app
        #from celery.app.control import inspect
        #from celery.shared_task.control import inspect
        insp = app.control.inspect()
        d = insp.stats()
        if not d:
            d = { ERROR_KEY: 'No running Celery workers were found.' }
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        d = { ERROR_KEY: msg }
    except ImportError as e:
        d = { ERROR_KEY: str(e)}
    return d
	
if __name__ == '__main__':
	d = get_celery_worker_status(); print(d)
    
