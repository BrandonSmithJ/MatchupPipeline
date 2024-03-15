from .. import app, utils

from collections import defaultdict as dd 
import subprocess,os

def get_active_tasks2(self,worker):
    """ Seems to not always get all tasks """
    inspector = app.control.inspect(destination=[worker])
    is_active = lambda t: ((t['name'] != 'shutdown') and 
                           (t['id']   != self.request.id))

    # Check all queues for remaining tasks
    for stage in ['active', 'scheduled', 'reserved']:
        sg = getattr(inspector, stage)()
        if sg is not None:
            for queue, tasks in sg.items():
                print(stage,queue,tasks)
                active = list(filter(is_active, tasks))
                if len(active): return len(active) 


def get_active_tasks(self,queues):

    # tasks = dd(list)
    with app.connection() as connection:
        with connection.channel() as channel:
            # inspector = app.control.inspect(connection=connection)

            # a = inspector.active_queues()
            # print(a)
            # for worker, queues in a.items():
            for queue in queues: #['celery', 'download','correct','extract','plot','write']: #'dedicated', 
            #for queue in ['celery', 'search','correct','extract','write']:

                name, jobs, consumers = channel.queue_declare(**{
                    'queue'   : queue,#['name'], 
                    'passive' : True,
                })
                
                print(name,jobs,consumers)
                if jobs > 0:
                    return jobs
                # active = []
                # parse  = lambda msg: msg.properties['application_headers']['task']
                # append = lambda msg: active.append( parse(msg) )
                # channel.basic_consume(**{
                #     'queue'    : queue,#['name'],
                #     'callback' : append,
                # })

                # for job in range(max(1, jobs)): connection.drain_events()
                # # print(f'{queue["name"]} ({jobs}, {name}): {active}')
                # print(f'{queue} ({jobs}, {name}): {active}')
                # print(inspector.active(), inspector.scheduled(), inspector.reserved())
                # print(inspector.stats())
    # return active 

import time

@app.task(bind=True, name='shutdown', priority=9)
def shutdown(self,queue=None,worker_name=None):
    """
    Shutdown the celery app once all task queues are empty.
    This task checks if there are other tasks in any queues,
    and if so, re-queues itself to check again in 10 seconds.

    Once all queues are found empty, it dispatches a message
    to stop the monitor, and a shutdown command to the app.
    """
    print("In shutdown...")
    print('Celery task ID is:',self.request.delivery_info['routing_key'],self.request.delivery_info)
    queue_OG = queue
    worker_OG = worker_name
    queue = queue.split(',')[-1]
    import socket
    socket_hostname = socket.gethostname()
    worker_name = worker_name.split('@')[0] + '@' + socket_hostname#hostname
    print("Queue:", queue, "Worker name", worker_name)

    active = get_active_tasks(self,[queue])  or get_active_tasks2(self,worker_name)
    # active = get_active_tasks(self)
    if active is not None:
        # count   = len(active)
        # message = f'Waiting for {count} {stage} tasks in {queue}'
        message = f'Waiting for {active} tasks'
        self.logger.info(message)
        self.logger.debug(f'Tasks: {active}')
        shutdown.apply_async(kwargs={'queue':queue_OG,'worker_name' :worker_OG},countdown=10,queue=queue)
        return


    # inspector = app.control.inspect()
    # is_active = lambda t: ((t['name'] != 'shutdown') and 
    #                        (t['id']   != self.request.id))

    # Check all queues for remaining tasks
    # for stage in ['active', 'scheduled', 'reserved']:
    #     for queue, tasks in getattr(inspector, stage)().items():
    #         active = list(filter(is_active, tasks))
    #         count  = len(active)

    #         # Requeue if there are remaining tasks (besides shutdown)
    #         if count:
    #             message = f'Waiting for {count} {stage} tasks in {queue}'
    #             self.logger.info(message)
    #             self.logger.debug(f'Tasks: {active}')
    #             shutdown.apply_async(countdown=10)
    #             return

    # Send message to the monitor that we're done
    with app.connection() as connection:
        dispatcher = app.events.Dispatcher(connection)
        dispatcher.send('stop-monitor')

    # Purge any remaining tasks in the queue
    utils.purge_queues(queues=[queue])

    self.logger.info(f'Finished all tasks; shutting down Celery app.')
    app.control.broadcast('shutdown', destination=[worker_name])
    #subprocess.check_output(['scancel', os.getenv('SLURM_JOB_ID')])

    #app.control.shutdown()
