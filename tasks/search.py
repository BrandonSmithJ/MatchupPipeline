from .. import API, app
from argparse import Namespace
from celery.contrib import rdb


def search(
    sample_config : dict,      # Config for this sample
    sensor        : str,       # Sensor to perform search for
    global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
    """ Search matching scene for a given sample """
    location = sample_config['location'] # Location object
    dt_range = sample_config['dt_range'] # DatetimeRange object
    out_path = global_config.output_path.joinpath('Scenes', sensor)

    api    = API.API[sensor]()
    scenes = api.search_scenes(sensor, location, dt_range)
    total_kwargs = []
    if len(scenes):
        for scene in list(scenes.keys()):

        
            # scene  = list(scenes.keys())[0] 
            kwargs = {
                'sensor'        : sensor,
                'scene_id'      : scene,
                'scene_details' : scenes[scene],
                'scene_folder'  : out_path,
                'overwrite'     : global_config.overwrite,
            }
            kwargs.update(sample_config)
            total_kwargs.append(kwargs)
    return total_kwargs

    # If there aren't any scenes found, break out of the pipeline chain
    # self.request.chain = None

@app.task(bind=True, name='download', queue='download')
def download(self,
    sample_config : dict,      # Config for this sample
    global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
    """ Download matching scene for a given sample """
    kwargs = {
        'sensor'        : sample_config['sensor'],
        'scene_id'      : sample_config['scene_id'],
        'scene_details' : sample_config['scene_details'],
        'scene_folder'  : sample_config['scene_folder'],
        'overwrite'     : global_config.overwrite,
    }
    out_path = sample_config['scene_folder']

    # Quick hack to minimize risk of running out of space
    try:
        folders = list(out_path.glob('*'))
        while (len(folders)>4000):
            import numpy as np
            import shutil
            oldest = min(folders, key=lambda f: f.stat().st_ctime)#i = np.random.randint(0, len(folders))
            shutil.rmtree(oldest) #folders[i].as_posix())
            folders = list(out_path.glob('*'))
    except Exception as e: print(e)#self.logger.error(f'Error removing folders: {e}')
    
    api    = API.API[sample_config['sensor']]()
    kwargs['scene_path'] = api.download_scene(**kwargs)
    kwargs.update(sample_config)
    return kwargs

