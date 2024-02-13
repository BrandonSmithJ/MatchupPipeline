from .. import app
from ..utils.write_complete import write_complete
from argparse import Namespace
from pathlib import Path
# import zarr
import numpy as np
import shutil

def serialize(values, separators=['||', '<>', ',']):
	""" Recursively serialize a nested list of values """
	if type(values) in [list, tuple, np.ndarray]:
		recurse = lambda v: serialize(v, separators[1:])
		return separators[0].join(map(recurse, values))
	return str(values)



@app.task(bind=True, name='write', queue='write', priority=4)
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
    
    out_path = global_config.output_path_local.joinpath(sample_config['dataset']).joinpath(sample_config['sensor']).joinpath(sample_config['ac_method']).joinpath('Matchups')
    print("Out path",out_path)
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
            if key in sample_config['scene_details'] and type(sample_config['scene_details']) != str:
                metadata_keys += [key]
                break
        if len(metadata_keys) > 5: break

    to_write['meta'] = serialize([
        sample_config[k] if k in sample_config else sample_config['scene_details'][k]
        for k in metadata_keys])
    
    if not out_path.joinpath('meta.csv').exists():
        with out_path.joinpath('meta.csv').open('a+') as f:
            f.write(f'{serialize(metadata_keys)}\n')

    for lat_i,lon_i,uid_i in zip(sample_config['lat'],sample_config['lon'],sample_config['uid']):
        lat_lon = '_'.join([str(lat_i),str(lon_i)])
        to_write[lat_lon] = {}
        to_write[lat_lon]['meta'] = serialize([uid_i,sample_config['datetime'],lat_i,lon_i,sample_config['scene_id']])


    for feature_dict in sample_config['extracted']:
        for lat_lon in feature_dict.keys():
            for feature, values in feature_dict[lat_lon].items():
                to_write[lat_lon][feature] = serialize(values)

                # with zarr.open(store=store, mode=mode) as group:
                # 	group[feature].append(np.array(values))
                # 	data = group.empty(dtype='array:float')
                # 	data.append(np.array(values))


    for ll_feature, ll_values  in to_write.items():
        if ll_feature == 'meta':
            continue
            #with out_path.joinpath(f'{ll_feature}.csv').open('a+') as f:
            #    f.write(f'{ll_values}\n')
        else:
            for feature, values in to_write[ll_feature].items(): 
                with out_path.joinpath(f'{feature}.csv').open('a+') as f:
                    f.write(f'{values}\n')

    try: 
        if global_config.remove_L2_tile: sample_config['correction_path'].unlink()
        if sample_config['ac_method'] == 'acolite':
            for suffix in ['L1R', 'L1R_pan', 'L2R']:
                for path in sample_config['correction_path'].glob(f'*{suffix}.nc'):
                    path.unlink()
        if global_config.remove_scene_folder: write_complete(scene_path=sample_config['scene_path'],ac_method=sample_config['ac_method'],ac_methods=global_config.ac_methods,out_string="Succes") #shutil.rmtree(sample_config['scene_path']) #print("Removeing scenes folder")#sample_config['scene_folder']sample_config['scene_path'].rmdir()
            
            
        return ["Finished Writing"]
    except Exception as e:
        with Path(__file__).parent.parent.joinpath('Logs', 'write_err.txt').open('a+') as f:
            f.write(f'Failed to remove nc files: {e}\n')
