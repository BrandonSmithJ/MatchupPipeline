from .. import app, utils

from collections import defaultdict as dd 


def get_active_tasks2(self):
    """ Seems to not always get all tasks """
    inspector = app.control.inspect()
    is_active = lambda t: ((t['name'] != 'shutdown') and 
                           (t['id']   != self.request.id))

    # Check all queues for remaining tasks
    for stage in ['active', 'scheduled', 'reserved']:
        sg = getattr(inspector, stage)()
        if sg is not None:
            for queue, tasks in sg.items():
                active = list(filter(is_active, tasks))
                if len(active): return len(active) 


def get_active_tasks(self):

    # tasks = dd(list)
    with app.connection() as connection:
        with connection.channel() as channel:
            # inspector = app.control.inspect(connection=connection)

            # a = inspector.active_queues()
            # print(a)
            # for worker, queues in a.items():
            for queue in ['celery', 'search','correct','extract','write']:
                name, jobs, consumers = channel.queue_declare(**{
                    'queue'   : queue,#['name'], 
                    'passive' : True,
                })
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
def shutdown(self):
    """
    Shutdown the celery app once all task queues are empty.
    This task checks if there are other tasks in any queues,
    and if so, re-queues itself to check again in 10 seconds.

    Once all queues are found empty, it dispatches a message
    to stop the monitor, and a shutdown command to the app.
    """
    active = get_active_tasks(self) or get_active_tasks2(self)
    # active = get_active_tasks(self)
    if active is not None:
        # count   = len(active)
        # message = f'Waiting for {count} {stage} tasks in {queue}'
        message = f'Waiting for {active} tasks'
        self.logger.info(message)
        self.logger.debug(f'Tasks: {active}')
        shutdown.apply_async(countdown=10)
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
    utils.purge_queues()

    self.logger.info(f'Finished all tasks; shutting down Celery app.') 
    app.control.shutdown()
