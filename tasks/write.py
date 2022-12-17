from .. import app
from argparse import Namespace
from pathlib import Path
# import zarr
import numpy as np


def serialize(values, separators=['||', '<>', ',']):
	""" Recursively serialize a nested list of values """
	if type(values) in [list, tuple, np.ndarray]:
		recurse = lambda v: serialize(v, separators[1:])
		return separators[0].join(map(recurse, values))
	return str(values)



@app.task(bind=True, name='write', queue='write')
def write(self,
    sample_config : dict,      # Config for this sample
    global_config : Namespace, # Config for the pipeline
) -> None:                     
    """ 
    Write the extracted window to disk. 
    Note that this function runs in a separate queue to ensure only
    one process ever handles writing (to avoid race conditions).
    """
    # dataset   = sample_config['dataset']
    # ac_method = 
    # sensor    = 
    to_write = {}

    # out_path.mkdir(exist_ok=True, parents=True)
    out_path = sample_config['output_path_full'].joinpath('Matchups')
    out_path.mkdir(exist_ok=True, parents=True)
    # sfile = out_path.joinpath('store.zarr')
    # mode  = 'a' if sfile.exists() else 'w'
    # store = zarr.DirectoryStore(sfile.as_posix())

    metadata_keys = ['uid', 'datetime', 'lat', 'lon', 'scene_id']
    for dt_key in ['start_time', 'begin_position', 'temporal_coverage', 'acquisition_date']:
        for transform in [
            lambda x: x,
            lambda x: x.replace('_', ''),
            lambda x: x[0] + x.title().replace('_', '')[1:]
        ]:
            key = transform(dt_key)
            if key in sample_config['scene_details']:
                metadata_keys += [key]
                break
        if len(metadata_keys) > 5: break

    to_write['meta'] = serialize([
        sample_config[k] if k in sample_config else sample_config['scene_details'][k]
        for k in metadata_keys])
    
    if not out_path.joinpath('meta.csv').exists():
        with out_path.joinpath('meta.csv').open('a+') as f:
            f.write(f'{serialize(metadata_keys)}\n')

    for feature_dict in sample_config['extracted']:
        for feature, values in feature_dict.items():
            to_write[feature] = serialize(values)

                # with zarr.open(store=store, mode=mode) as group:
                # 	group[feature].append(np.array(values))
                # 	data = group.empty(dtype='array:float')
                # 	data.append(np.array(values))


    for feature, values in to_write.items():
        with out_path.joinpath(f'{feature}.csv').open('a+') as f:
            f.write(f'{values}\n')

    try: 
        if remove_L2_tile: sample_config['correction_path'].unlink()
        if sample_config['ac_method'] == 'acolite':
            for suffix in ['L1R', 'L1R_pan', 'L2R']:
                for path in sample_config['correction_path'].glob(f'*{suffix}.nc'):
                    path.unlink()
    except Exception as e:
        with Path(__file__).parent.parent.joinpath('Logs', 'write_err.txt').open('a+') as f:
            f.write(f'Failed to remove nc files: {e}\n')
