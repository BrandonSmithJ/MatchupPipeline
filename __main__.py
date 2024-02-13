from itertools import product
from datetime import timedelta as td
from argparse import Namespace
from pathlib import Path
import pandas as pd
import numpy as np
from .tasks import create_extraction_pipeline, CeleryManager
from .utils import pretty_print, color
from .utils import Location, DatetimeRange
from .parameters import get_args
from .tasks.search  import search
from subprocess import getoutput
username = getoutput('whoami')
from multiprocessing import Process
import time
import math
import shutil
#import app as app2
import random
def load_insitu_data(global_config : Namespace) -> pd.DataFrame:
    """ Load the in situ data and parse as necessary """
    datasets = []
    ins_path = Path(global_config.insitu_path)
    
    
    for dataset in global_config.datasets:
        current_dataset = []
        path = ins_path.joinpath(dataset, 'parsed.csv')
        
        #Check if dataset file already exists
        dataset_path = ins_path.joinpath(dataset,'_'.join(sorted(global_config.sensors))+'_dataset.pkl') #sensors
        if dataset_path.exists() and not global_config.overwrite:
            current_dataset=pd.read_pickle(dataset_path)
            current_dataset = [rows.to_frame().swapaxes("index","columns") for index, rows in current_dataset.iterrows()]
            datasets.append(current_dataset)
            continue
        assert(path.exists()), f'Dataset missing required file: {path}'

        try:
            try:    data = pd.read_csv(path, parse_dates=['date']).dropna()
            except: data = pd.read_csv(path, parse_dates=['datetime']).dropna()

            if 'time' in data.columns:
                data['datetime'] = data['date'].astype(str) + ' ' + data['time']

            # Assume 'date' columns don't contain valid time information
            if 'datetime' not in data.columns:
                data['datetime'] = data['date'].dt.date

            dts = pd.to_datetime(data['datetime'])
            data['date']     = dts.dt.date
            data['datetime'] = pd.Series(dts.dt.to_pydatetime(), dtype=object).values

            # Need to ensure uid is actually unique
            idxs = pd.Series(np.arange(len(data))).astype(str)
            if 'uid' not in data: data['uid'] = idxs

            data['uid'] = data['uid'].astype(str)
            if not data['uid'].is_unique:
                data['uid'] = idxs+ '_' + data['uid']
            data['uid'] = dataset + '_' + data['uid']
            data['dataset'] = dataset
            data['lat'] = data['lat'].apply(lambda x: float(x.replace('/','')) if type(x) == str else x)
            data['lon'] = data['lon'].apply(lambda x: float(x.replace('/','')) if type(x) == str else x)

            # Parse Location objects
            data['location'] = data.apply(lambda row:
                Location(**({
                    'footprint' : row['footprint']
                } if 'footprint' in row else dict(
                    zip(['n','s','e','w'], [float(i) for i in row['Coordinates_n_s_e_w'].split(' ')])
                ) if 'Coordinates_n_s_e_w' in row else {
                    'lat' : row['lat'],
                    'lon' : row['lon'],
                })),
            axis=1)

            # Parse DatetimeRange objects

            if global_config.search_day_window is not None or global_config.search_minute_window is not None :
                sdw    = global_config.search_day_window
                smw    = global_config.search_minute_window
                window = smw or (sdw * 24 * 60) # Convert to minutes
                data['dt_range'] = data.apply(lambda row:
                DatetimeRange(center=row['datetime'], window=td(minutes=window)),
                axis=1)
            if global_config.search_year_range is not None:
                data['dt_range'] = data.apply(lambda row:
                DatetimeRange(start=row['datetime'], end=row['datetime'] + td(minutes=global_config.search_year_range*24*60*365)),
                axis=1)           

        except Exception as e: 
            raise Exception(f'Could not parse {path}: {e}')
        j=0
        if global_config.timeseries_or_matchups == 'timeseries':
            for i, row in data.iterrows():
                for sensor in global_config.sensors: 
                    data_kwargs =search(sample_config=row.to_dict(),sensor=sensor,global_config = global_config)
                    for data_kwarg in data_kwargs:
                        data_kwarg['scene_details'] =  str(data_kwarg['scene_details'])
                        current_dataset.append(pd.DataFrame.from_dict([data_kwarg])) 
                        if not j%10: print(f"Searched {j} Matchups")
                        j= j + 1
                    
            pd.concat(current_dataset).to_pickle(dataset_path)
            datasets.append(current_dataset)
            datasets = [dataframe for sub_dataset in datasets for dataframe in sub_dataset]
            #return pd.concat(datasets)
 
        if global_config.timeseries_or_matchups == 'matchups':
             datasets.append(data)
             
    if dataset_path.exists() and global_config.timeseries_or_matchups == 'timeseries':
        datasets = []
        current_dataset=pd.read_pickle(dataset_path)
        current_dataset = [rows.to_frame().swapaxes("index","columns") for index, rows in current_dataset.iterrows()]
        datasets.append(current_dataset)
 
    def set_func(inp):
        unique_values = set(inp)
        if len(unique_values) == 1:
            unique_values = list(unique_values)[0]
        else:
            assert(0)
        return unique_values

    datasets_grouped = {}
    for key in [ i for i in pd.concat(datasets[0]).keys().to_list() if i != 'scene_id']: 
        datasets_grouped[key]      = pd.concat(datasets[0]).groupby('scene_id')[key].apply(list).reset_index(name=key)
        if key in ['sensor',  'scene_details', 'scene_folder', 'overwrite', 'datetime', 'Provider', 'date', 'dataset']:
            datasets_grouped[key][key] = datasets_grouped[key][key].map(set_func)
   
    datasets_grouped_out = datasets_grouped['sensor'].set_index('scene_id')
    
    for key in [i for i in datasets_grouped.keys() if i !='sensor']: 
        datasets_grouped_out       = datasets_grouped_out.join(datasets_grouped[key].set_index('scene_id'))
   
    datasets_grouped_out['scene_id'] = datasets_grouped_out.index
    
    if global_config.timeseries_or_matchups == 'matchups': return pd.concat(datasets)
    if global_config.timeseries_or_matchups == 'timeseries' and dataset_path.exists(): return datasets_grouped_out #pd.concat(datasets[0])


def filter_completed(
    global_config : Namespace, 
    data          : pd.DataFrame,
) -> pd.DataFrame:
    """ Remove already completed samples from the data """
    get_path = lambda parts: global_config.output_path.joinpath(*parts)
    get_name = lambda  path: path.relative_to(global_config.output_path).parent
    all_path = lambda *sets: map(get_path, product(*sets))
    
    get_exists = lambda f, *p: list(filter(Path.exists, all_path(*p, [f])))
    read_files = lambda p,**k: [pd.read_csv(path, **k) for path in p]

    datasets   = global_config.datasets
    sensors    = global_config.sensors 
    ac_methods = global_config.ac_methods

    completed_files = get_exists('completed.csv', datasets, sensors)
    completed_uids  = read_files(completed_files, index_col=None, header=None)

    if len(completed_uids):
        completed   = pd.concat(completed_uids)
        uids, found = completed.iloc[:, 0], completed.iloc[:, 1]
        found = found.replace({' True': True, ' False': False})

        matched  = uids.loc[ found] 
        no_match = uids.loc[~found] 

        metapaths = get_exists('meta.csv', datasets, sensors, ac_methods,['Matchups'])
        metanames = map(get_name, metapaths)
        written   = [df['scene_id'] for df in read_files(metapaths, **{
            'index_col' : None,
            'header'    : 0,
            'delimiter' : '\|\|',
            'engine'    : 'python',
        })]

        process_count  = color(f'{len(uids.unique()):,}', 'blue')
        matched_count  = color(f'{len( matched.unique()):,}', 'cyan')
        no_match_count = color(f'{len(no_match.unique()):,}', 'magenta')

        print(f'Total samples currently processed: {process_count}')
        print(f'  Samples with matching scene:    { matched_count}')
        print(f'  Samples without matching scene: {no_match_count}')
        print(f'\nSamples currently written for each data source: ',end='')
        print(pretty_print(dict(zip(metanames,map(len, written)))), end='\n\n')

        if len(written):
            written  = pd.concat(written)
            matched  = matched[matched.isin(written.unique())]
            complete = pd.concat([no_match, matched]).unique()
        else: complete = no_match
    else:     complete = []

    total_count = color(f'{len(data):,}', 'blue') 
    done_count  = color(f'{len(complete):,}', 'green')
    left_count  = color(f'{len(data) - len(complete):,}', 'red')
    print(f'Total samples found: {total_count}')
    print(f'   Currently completed: {done_count}')
    print(f'  Remaining to process: {left_count}\n')


    def uid_str(inp):
        return '-'.join([i if j == 0 else i.split('_')[-1] for j,i in enumerate(sorted(inp)) ])

    data['uid_str'] = data['uid'].map(uid_str) if type( data['uid'][0]) is list else data['uid']
    if global_config.timeseries_or_matchups !='matchups':
        data['complete_id'] = data['scene_id'] #data['uid_str']+'-'+data['scene_id']
    else:
        data['complete_id'] = data['uid_str']
    
    # Processes only files successfully processed by another program
    if global_config.filter_unprocessed_imagery:
        meta_files = get_exists('meta.csv', datasets, sensors,['aquaverse'],['Matchups'])
        meta_uids = read_files(meta_files, index_col=None, header=0, delimiter="|")[0]['uid'].values
        complete = [completed.split('-')[0] for completed in complete]
        return data.loc[data['uid'].isin(meta_uids)*~data['complete_id'].isin(complete)]
    

    return data.loc[~data['complete_id'].isin(complete)]


def update_app(user_flag, app):
    cert_root = '/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/rabbitMQ/rabbitmq_server_files/TLS'
    if os.path.exists(cert_root):
      import ssl
      app.conf.update(**{
        #'broker_url'     :f'pyamqp://{username}:mp{username}@localhost:5671/matchups_{username}', # it works!!
        'broker_url'     :f'pyamqp://{username}_{user_flag}:mp{username}_{user_flag}@pardees:5671/matchups_{username}_{user_flag}', 
        'broker_use_ssl' : {
          'keyfile'    : f'{cert_root}/server-key.pem',
          'certfile'   : f'{cert_root}/server-cert.pem',
          'ca_certs'   : f'{cert_root}/ca-cert.pem',
          'cert_reqs'  : ssl.CERT_REQUIRED,
        },
      })
    return app

# Debug changes celery to implement tasks in serial instead of parallel, must also set ALWAYS_EAGER to True in init file
def main2(gc, data, i, debug=True):
    # # Shuffle samples to minimize risk of multiple threads trying to operate
    # # on the same matching scene at once
    from pathlib import Path
    Path(Path(__file__).parent.joinpath('Logs').joinpath(username)).mkdir(parents=True, exist_ok=True)
    worker_kws = [
        # Multiple threads for download
        {   'logname'     : f'{username}/worker1{i}',
            'queues'      : ['search','download','correct','extract','plot','celery','write'],
            #'queues'      : ['search', 'celery'],
            'concurrency' : 4,
            'slurm_kwargs': {'partition' : 'ubuntu20','exclude':'slrm[0001-0048]'},
        },
        # Multiple threads for correction
        #{   'logname'     : f'{username}/worker2{i}',
        #    'queues'      : ['correct'],
        #    'concurrency' : 4, #
        #    'slurm_kwargs': {'partition' : 'ubuntu20','exclude':'slrm[0005-0055]'},
        #},
        # Single dedicated thread (i.e. for writing)
        #{   'logname'     : f'{username}/worker3{i}',
        #    'queues'      : ['write'],
        #    'concurrency' : 1,
        #    'slurm_kwargs': {'partition' : 'ubuntu20','exclude':'slrm[0005-0055]'},
        #},
    ]
    pipeline = create_extraction_pipeline(gc)
    with CeleryManager(worker_kws, data, gc.ac_methods) as manager:
        #for i, row in data.iterrows(): 
        #if debug: print(data['scene_id'],gc.scene_id)
        #if gc.scene_id in data['scene_id']: #'T18SUG' '044033' 'T2017252150500'
        data = data.to_dict()
        if debug and gc.timeseries_or_matchups !='matchups': print(data['scene_id'],gc.scene_id)
        #data = data.to_dict()
        if 'scene_id' in data.keys():
            if gc.scene_id not in data['scene_id']: return 0#'T18SUG' '044033' 'T2017252150500'
        #data = data.to_dict()
        pipeline(data) if debug else pipeline.delay(data)
        #time.sleep(10)

        # deploy_job.sh {row} - how? This should call a python script to start processing
                # row.pkl 
                # strt slrm jobs - activats env
                # run main.py - starts celery/rabbitMQ? not able to start them from a slurm job.
                # main row.pkl
                
    # pass this celery processing to each node
    # deploy_job.sh that will receive each row elements 
    # and create an instance of "pipeline" object and run in parallel

def main(debug=True):
    global_config = gc = get_args()
    print(f'\nRunning pipeline with parameters: {pretty_print(gc.__dict__)}\n')
    data = load_insitu_data(gc)
    data = filter_completed(gc, data)
    
    assert(len(data))

    # Shuffle samples to minimize risk of multiple threads trying to operate
    # on the same matching scene at once
    data = data.sample(frac=1)
    #j = 0
    #for j in range(math.ceil(len(data)/20)):
    #    data2 = data.iloc[j:j+20,:]
    #    for i in range(math.ceil(len(data2))): # len of the parsed
    #        p = Process(target=main2, args=(gc, data2.iloc[i], str(i)))
    #        p.start()
    #        time.sleep(60*2)
    
    #        folders = list(out_path.glob('*'))
    #    if (len(folders)>global_config.max_processing_scenes):
    out_path = global_config.output_path.joinpath(global_config.sensors[0])
    print("Outpath is")
    print(out_path)
    list_range = list(range(len(data)))
    random_list_range = random.shuffle(list_range)
    print(list_range)
    processes = []
    max_jobs  = 3
    finished_processing = 0
    #print(random_list_range)
    for i,j in enumerate(list_range):
        #print(j,data.iloc[j])
        folders = list(out_path.glob('*'))
        #while (len(folders)>global_config.max_processing_scenes):
        #    time.sleep(60*2)
        #    folders = list(out_path.glob('*'))
        #    print("Too many output folders")

        p = Process(target=main2, args=(gc, data.iloc[j], str(j)))
        p.start()
        processes.append(p)
        #p.join()

        time.sleep(30*1)
        if i >= 2*max_jobs-1:
            [proc.join() for proc in processes[finished_processing*max_jobs:(finished_processing+1)*max_jobs]]
            finished_processing = finished_processing+1
    [ process.join() for process in processes if process.is_alive()]
    

def main_local(debug=True):
    global_config = gc = get_args()
    print(f'\nRunning pipeline with parameters: {pretty_print(gc.__dict__)}\n')

    pipeline = create_extraction_pipeline(gc)

    data = load_insitu_data(gc)
    data = filter_completed(gc, data)
    assert(len(data))

    # Shuffle samples to minimize risk of multiple threads trying to operate
    # on the same matching scene at once
    data = data.sample(frac=1)
    print(data, '\n')
    from pathlib import Path
    Path(Path(__file__).parent.joinpath('Logs').joinpath(username)).mkdir(parents=True, exist_ok=True)
    worker_kws = [
        # Multiple threads for download
        {   'logname'     : f'{username}/worker1',
            'queues'      : ['search','download','correct','extract','plot','celery'],
            'concurrency' : 2,
        },
        # Multiple threads for correction
        {   'logname'     : f'{username}/worker2',
            'queues'      : ['correct'],
            'concurrency' : 8,
        },
        # Multiple threads for extraction
        {   'logname'     : f'{username}/worker3',
            'queues'      : ['extract'],
            'concurrency' : 1,
        },
        # Multiple threads for plotting
        {   'logname'     : f'{username}/worker4',
            'queues'      : ['plot'],
            'concurrency' : 2,
        },
        # Single dedicated thread (i.e. for writing)
        {   'logname'     : f'{username}/worker5',
            'queues'      : ['write'],
            'concurrency' : 1,
        },
    ]
    #assert(0)
    with CeleryManager(worker_kws, data, gc.ac_methods) as manager:
        for i, row in data.iterrows():
            if debug and global_config.timeseries_or_matchups !='matchups': print(row['scene_id'],global_config.scene_id)
            if 'scene_id' in row.keys():
                if global_config.scene_id not in row['scene_id']: continue#'T18SUG' '044033' 'T2017252150500'
            row = row.to_dict()
            pipeline(row) if debug  else pipeline.delay(row)



if __name__ == '__main__':
    main()
        

    '''
    Todo:
     - TM tests
     - documentation / formatting / tab->space wrap up
     - double check all Worker functionality is migrated
    Eventually:
     - migration to zarr
     - better monitoring (plotext) / logging
     - plotting functionality task / pipeline (hand over to Ryan?)
     - more tests / validate other sensors
     - validate polymer (+polymer cleanup)
    '''
    
    # How to set up slurm 
    # deploy_job can call this main with 1 row first
    
    # To set up slurm without celery/rabbitMQ 
    # Search the API --> all the sceneids- info
    # deploy jobs with info
    # download file on the compute node
    # process - serially might not work due to time limit
    # Four processors can be submitted in different slurm job    


