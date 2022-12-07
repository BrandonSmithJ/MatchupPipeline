# Required by Windows
import os 
os.environ['FORKED_BY_MULTIPROCESSING'] = '1'

# Define NCCS flag to indicate SLURM usage
import socket
NCCS = 'discover' in socket.gethostname()

# Define our celery application
from celery import Celery 
task = 'pipeline.tasks.pipelines.PipelineTask:PipelineTask'
app  = Celery('pipeline', task_cls=task)

# Set configuration options
# https://docs.celeryq.dev/en/stable/userguide/configuration.html
app.conf.update(**{
    'broker_url'              : 'pyamqp://localhost',
    'result_backend'          : 'rpc://localhost',
    'timezone'                : 'America/New_York',
    'task_serializer'         : 'pickle',
    'result_serializer'       : 'pickle',
    'accept_content'          : ['pickle'],
    'imports'                 : ['pipeline.tasks'],

    'result_extended'         : True, # Enables extended task result attributes
    'worker_send_task_events' : True, # Send task-related events for Flower

    'task_acks_late' : True,
    'worker_prefetch_multiplier' : 1,
})

# Set task routes
app.conf.task_routes = {
   'search'  : {'queue': 'search'},
   'correct' : {'queue': 'correct'},
   'extract' : {'queue': 'extract'},
   'write'   : {'queue': 'write'},
}

# If we're on pardees, we're using TLS for RabbitMQ
cert_root = '/discover/nobackup/bsmith16/Matchups_Files/TLS'
if os.path.exists(cert_root):
  import ssl
  app.conf.update(**{
    'broker_url'     : 'pyamqp://bsmith16:mpbsmith16@discover34:5671',
    #'broker_url'     : 'pyamqp://rabbit@discover34:5671/matchups_bsmith16',
    'broker_use_ssl' : {
      'keyfile'    : f'{cert_root}/server-key.pem',
      'certfile'   : f'{cert_root}/server-cert.pem',
      'ca_certs'   : f'{cert_root}/ca-cert.pem',
      'cert_reqs'  : ssl.CERT_REQUIRED,
    },
  })


