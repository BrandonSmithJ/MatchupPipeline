from .. import API, app
from argparse import Namespace


@app.task(bind=True, name='search', queue='search', priority=1)
def search(self,
    sample_config : dict,      # Config for this sample
    sensor        : str,       # Sensor to perform search for
    global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
    """ Search and download matching scene for a given sample """
    location = sample_config['location'] # Location object
    dt_range = sample_config['dt_range'] # DatetimeRange object
    out_path = global_config.output_path.joinpath('Scenes', sensor)

    api    = API.API[sensor]()
    scenes = api.search_scenes(sensor, location, dt_range)

    if len(scenes):
        # Quick hack to minimize risk of running out of space
        try:
            folders = list(out_path.glob('*'))
            if len(folders) > 50:
                import numpy as np
                import shutil
                oldest = min(folders, key=lambda f: f.stat().st_ctime)#i = np.random.randint(0, len(folders))
                shutil.rmtree(oldest) #folders[i].as_posix())
        except Exception as e: self.logger.error(f'Error removing folders: {e}')

        scene  = list(scenes.keys())[0] 
        kwargs = {
            'sensor'        : sensor,
            'scene_id'      : scene,
            'scene_details' : scenes[scene],
            'scene_folder'  : out_path,
            'overwrite'     : global_config.overwrite,
        }
        kwargs['scene_path'] = api.download_scene(**kwargs)
        kwargs.update(sample_config)
        return kwargs

    # If there aren't any scenes found, break out of the pipeline chain
    self.request.chain = None
