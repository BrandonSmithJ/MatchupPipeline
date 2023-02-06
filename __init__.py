# Required by Windows
import os 
os.environ['FORKED_BY_MULTIPROCESSING'] = '1'

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
    'task_always_eager' : True, # Processes in serial, locally 

})

# Set task routes
app.conf.task_routes = {
   'download': {'queue': 'download'},
   'correct' : {'queue': 'correct'},
   'extract' : {'queue': 'extract'},
   'plot'    : {'queue': 'plot'},
   'write'   : {'queue': 'write'},
}

# If we're on pardees, we're using TLS for RabbitMQ
cert_root = '/home/bsmith16/workspace/rabbitmq_server-3.10.7/etc/pki/tls'
#cert_root = '/home/roshea/rabbitMQ/rabbitmq_server-3.10.7/etc/pki/tls'
if os.path.exists(cert_root):
  import ssl
  app.conf.update(**{
    'broker_url'     :'pyamqp://localhost:5671' ,#'pyamqp://roshea:password@localhost:5671/IP_4', #'pyamqp://roshea:password@localhost:5671/IP_1'
    'broker_use_ssl' : {
      'keyfile'    : f'{cert_root}/server-key.pem',
      'certfile'   : f'{cert_root}/server-cert.pem',
      'ca_certs'   : f'{cert_root}/ca-cert.pem',
      'cert_reqs'  : ssl.CERT_REQUIRED,
    },
  })


