from .. import API, app
from argparse import Namespace


@app.task(bind=True, name='search', queue='search', priority=1)#, rate_limit='3/m')
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
            folders = [f for f in out_path.glob('*') if f.joinpath('.complete').exists()]
            
            if len(folders) > 20:
                import numpy as np
                import shutil
                # Doesn't work on linux?
                #oldest = min(folders, key=lambda f: f.stat().st_ctime)#i = np.random.randint(0, len(folders))
                oldest = min(folders, key=lambda f: min(f.joinpath('.complete').stat().st_ctime, f.joinpath('.complete').stat().st_atime))
                #parse_f = lambda f: dt.fromtimestamp(min(f.stat().st_ctime, f.stat().st_atime))
                #options = {f.name: parse_f(f.joinpath('.complete')) for f in folders}
                #self.logger.info(f'Removing folder {oldest} out of options: \n{pretty_print(options)}')
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
        self.logger.info(f'Downloading scene {scene}')
        kwargs['scene_path'] = api.download_scene(**kwargs)
        kwargs.update(sample_config)
        return kwargs

    # If there aren't any scenes found, break out of the pipeline chain
    self.request.chain = None
