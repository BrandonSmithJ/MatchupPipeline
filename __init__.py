#<<<<<<< HEAD
# Required by Windows
import os 
os.environ['FORKED_BY_MULTIPROCESSING'] = '1'

#from .parameters import get_args

#global_config = gc = get_args()

# Define NCCS flag to indicate SLURM usage
import socket
NCCS = 'pardees' in socket.gethostname()

# Define our celery application
from celery import Celery 
from subprocess import getoutput 
username = getoutput('whoami')

task = 'pipeline.tasks.pipelines.PipelineTask:PipelineTask'
app  = Celery('pipeline', task_cls=task)
#app.control.inspect().active()

# Set configuration options
# https://docs.celeryq.dev/en/stable/userguide/configuration.html
app.conf.update(**{
    'broker_url'              : 'pyamqp://pardees:5671', #5671 is not default; 5672 is localhost
    'result_backend'          : 'rpc://pardees:5671',
    
    #'broker_url'              : 'pyamqp://skabir:skabir@pardees:5672',
    #'result_backend'          : 'rpc://skabir:skabir@pardees:5672',
    #'result_backend'          : f'rpc://{username}:mp{username}@localhost:5671',
    
    'timezone'                : 'America/New_York',
    'task_serializer'         : 'pickle',
    'result_serializer'       : 'pickle',
    'accept_content'          : ['pickle'],
    'imports'                 : ['pipeline.tasks'],

    'result_extended'         : True, # Enables extended task result attributes
    'worker_send_task_events' : True, # Send task-related events for Flower
    'event_queue_ttl' :30,
    
    'task_acks_late' : False,
    'worker_prefetch_multiplier' : 1,
    
    'task_queue_max_priority' : 10,
    'task_queue_default_priority' : 5,

    'task_always_eager' : False, # Processes in serial, locally 
})
# Need to allow larger representations to reconstruct arguments in the
# Monitor. Otherwise, [kw]args are cutoff with '...' after certain length
app.amqp.argsrepr_maxsize = 32768
app.amqp.kwargsrepr_maxsize = 32768

# Set task routes
app.conf.task_routes = {
   'search'  : {'queue': 'search'},
   'download': {'queue': 'download'},
   'correct' : {'queue': 'correct'},
   'extract' : {'queue': 'extract'},
   'plot'    : {'queue': 'plot'},
   'write'   : {'queue': 'write'},
}
from kombu import Exchange, Queue
app.conf.task_queues = [
        Queue('search',  Exchange('search'),  routing_key='search'  ,queue_arguments={'x-max-priority': 10}, consumer_arguments={'x-priority': 0}),
        Queue('download',Exchange('download'),routing_key='download',queue_arguments={'x-max-priority': 10}, consumer_arguments={'x-priority': 1}),
        Queue('correct', Exchange('correct'), routing_key='correct' ,queue_arguments={'x-max-priority': 10}, consumer_arguments={'x-priority': 2}),
        Queue('extract', Exchange('extract'), routing_key='extract' ,queue_arguments={'x-max-priority': 10}, consumer_arguments={'x-priority': 3}),
        Queue('plot'   , Exchange('plot'),    routing_key='plot'    ,queue_arguments={'x-max-priority': 10}, consumer_arguments={'x-priority': 4}),
        Queue('write',   Exchange('write'),   routing_key='write'   ,queue_arguments={'x-max-priority': 10}, consumer_arguments={'x-priority': 5}),
]
# If we're on pardees, we're using TLS for RabbitMQ
#cert_root = '/home/bsmith16/workspace/rabbitmq_server-3.10.7/etc/pki/tls'
#cert_root = '/home/roshea/rabbitMQ/rabbitmq_server-3.10.7/etc/pki/tls'
#cert_root = '/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/rabbitMQ/RabbitMQ/rabbitmq_server-3.12.6/etc/pki/tls'

# cert_root = '/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/rabbitMQ/rabbitmq_server_files/TLS'
# if os.path.exists(cert_root):
  # import ssl
  # app.conf.update(**{
    # #'broker_url'     :f'pyamqp://{username}:mp{username}@localhost:5671/matchups_{username}', # it works!!
    # 'broker_url'     :f'pyamqp://{username}_{user_flag}:mp{username}_{user_flag}@pardees:5671/matchups_{username}_{user_flag}', 
    # 'broker_use_ssl' : {
      # 'keyfile'    : f'{cert_root}/server-key.pem',
      # 'certfile'   : f'{cert_root}/server-cert.pem',
      # 'ca_certs'   : f'{cert_root}/ca-cert.pem',
      # 'cert_reqs'  : ssl.CERT_REQUIRED,
    # },
  # })
#test_suffix = '_test' if global_config.test_pipeline_celery else ''

test = False
cert_root = '/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/rabbitMQ/rabbitmq_server_files/TLS'
if os.path.exists(cert_root):
  import ssl
  app.conf.update(**{
    #'broker_url'     :f'pyamqp://{username}:mp{username}@localhost:5671/matchups_{username}', # it works!!
    'broker_url'     :f'pyamqp://{username}_test:mp{username}_test@pardees:5671/matchups_{username}_test' if test else f'pyamqp://{username}:mp{username}@pardees:5671/matchups_{username}', 
    'broker_use_ssl' : {
      'keyfile'    : f'{cert_root}/server-key.pem',
      'certfile'   : f'{cert_root}/server-cert.pem',
      'ca_certs'   : f'{cert_root}/ca-cert.pem',
      'cert_reqs'  : ssl.CERT_REQUIRED,
    },
  })
