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



def load_insitu_data(global_config : Namespace) -> pd.DataFrame:
    """ Load the in situ data and parse as necessary """
    datasets = []
    ins_path = Path(global_config.insitu_path)

    for dataset in global_config.datasets:
        path = ins_path.joinpath(dataset, 'parsed.csv')
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
            data['datetime'] = pd.Series(dts.dt.to_pydatetime(), dtype=object)

            # Need to ensure uid is actually unique
            idxs = pd.Series(np.arange(len(data))).astype(str)
            if 'uid' not in data: data['uid'] = idxs

            data['uid'] = data['uid'].astype(str)
            if not data['uid'].is_unique:
                data['uid'] = idxs+ '_' + data['uid']
            data['uid'] = dataset + '_' + data['uid']
            data['dataset'] = dataset

            # Parse Location objects
            data['location'] = data.apply(lambda row:
                Location(**({
                    'footprint' : row['footprint']
                } if 'footprint' in row else dict(
                    zip(['nsew'], row['Coordinates_n_s_e_w'])
                ) if 'Coordinates_n_s_e_w' in row else {
                    'lat' : row['lat'],
                    'lon' : row['lon'],
                })),
            axis=1)

            # Parse DatetimeRange objects
            sdw    = global_config.search_day_window
            smw    = global_config.search_minute_window
            window = smw or (sdw * 24 * 60) # Convert to minutes
            data['dt_range'] = data.apply(lambda row:
                DatetimeRange(center=row['datetime'], window=td(minutes=window)),
            axis=1)

        except Exception as e: 
            raise Exception(f'Could not parse {path}: {e}')

        datasets.append(data)
    return pd.concat(datasets)



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

        metapaths = get_exists('meta.csv', datasets, sensors, ac_methods)
        metanames = map(get_name, metapaths)
        written   = [df['uid'] for df in read_files(metapaths, **{
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
    return data.loc[~data['uid'].isin(complete)]


#debug changes celery to implement tasks in serial instead of parallel
def main(debug=True):
    global_config = gc = get_args()
    print(f'\nRunning pipeline with parameters: {pretty_print(gc.__dict__)}\n')

    pipeline = create_extraction_pipeline(gc)

    data = load_insitu_data(gc)
    data = filter_completed(gc, data)
    assert(len(data))

    #from datetime import datetime as dt
    #data = data.loc[pd.to_datetime(data['datetime']).dt.date >= dt(2009,3,26).date()]
    


    # Shuffle samples to minimize risk of multiple threads trying to operate
    # on the same matching scene at once
    data = data.sample(frac=1)
    print(data, '\n')

    worker_kws = [
        # Multiple threads for search
        {   'logname'     : 'worker1',
            'queues'      : ['search', 'celery'],
            'concurrency' : 2,
        },
        # Multiple threads for correction
        {   'logname'     : 'worker2',
            'queues'      : ['correct'],
            'concurrency' : 4,
        },
        # Multiple threads for extraction
        {   'logname'     : 'worker3',
            'queues'      : ['extract'],
            'concurrency' : 3,
        },
        # Single dedicated thread (i.e. for writing)
        {   'logname'     : 'worker4',
            'queues'      : ['write'],
            'concurrency' : 1,
        },
    ]
    
    with CeleryManager(worker_kws, data, gc.ac_methods) as manager:
        for i, row in data.iterrows():
            #row['location'] = Location(lat=47.443, lon=-61.8168)
            #print(row)
            #print()
            #print('Running:',manager.running())
            pipeline(row.to_dict()) if debug  else pipeline.delay(row.to_dict())
            # if i >= 10: break


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
