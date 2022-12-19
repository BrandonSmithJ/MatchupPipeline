from .. import app 



def purge_queues(
    queues=['celery', 'dedicated', 'download', 'correct', 'extract', 'plot', 'write'],
):
    """ Attempt to purge all celery queues """
    with app.connection_for_write() as conn:
        for queue in queues:
            try:    conn.default_channel.queue_purge(queue)
            except: pass
    app.control.purge()
