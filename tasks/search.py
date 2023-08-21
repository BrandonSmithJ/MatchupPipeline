from .. import API, app
from argparse import Namespace
from celery.contrib import rdb
from ..utils.run_subprocess import run_subprocess


@app.task(bind=True, name='search', queue='search', priority=0)#, rate_limit='1/m')
def search(self,
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
    return kwargs if global_config.timeseries_or_matchups == 'matchups' else total_kwargs

    # If there aren't any scenes found, break out of the pipeline chain
    # self.request.chain = None

def run_aquaverse_download(scene_id,sensor,output_folder,stream_backend_path,stream_env_path,AQV_location,location="Bay",timeout=3600,overwrite=False):
    import csv, os,time
    from pathlib import Path
    from subprocess import Popen, PIPE, check_output, STDOUT
    
    AQV_download = AQV_location+'/download_AQV'
    scene_output = str(output_folder)+'/'+scene_id +'/' 
    Path(scene_output).mkdir(parents=True,exist_ok=True)
    #Checks if the scene is already downloaded
    downloaded_file = '/tis/stream/data/' + scene_id + '.tar.gz'
    
    if not os.path.exists(downloaded_file) or overwrite:
        aquaverse_csv_filename = scene_output + 'aquaverse_scene.csv'
        print(aquaverse_csv_filename)
        with open(aquaverse_csv_filename, 'w', newline='') as csvfile:
            row_writer = csv.writer(csvfile, delimiter=',')
            row_writer.writerow([scene_id,location])
            
        #activates environment and runs download, waiting for return (timeout)
        running_procs = Popen([AQV_download, str(stream_backend_path), str(stream_env_path), str(aquaverse_csv_filename), '-redownload' ,str(sensor)], stdout=PIPE, stderr=PIPE)
        run_subprocess(running_procs,timeout=timeout)
        start = time.time()
        while not os.path.exists(downloaded_file) and time.time()-start < timeout:
            print("Waiting for output... ", time.time()-start , "seconds")
            time.sleep(30)

def run_aquaverse_pull_tar(scene_id, AQV_location,output_folder,timeout=600):
    from subprocess import Popen, PIPE, check_output, STDOUT
    from pathlib import Path
    AQV_pull_tar = AQV_location+'/pull_tar_AQV'
    scene_output = str(output_folder)+'/'+scene_id +'/'
    running_procs = Popen([AQV_pull_tar, str(scene_id), str(scene_output) ], stdout=PIPE, stderr=PIPE)
    run_subprocess(running_procs,timeout=timeout)
    
    # finds and unpacks tar
    import tarfile
    print('Unziping tar file ...')
    scene_id_path = str(output_folder) + '/' + scene_id + '/'
    tar_path = scene_id_path + scene_id +'.tar.gz'
    tar = tarfile.open(tar_path)
    tar.extractall(scene_id_path)
    tar.close()
    Path(scene_id_path).joinpath('.complete').touch()
    
    
@app.task(bind=True, name='download', queue='download',priority=0)
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
        while (len(folders)>200):
            import numpy as np
            import shutil
            oldest = min(folders, key=lambda f: f.stat().st_ctime)#i = np.random.randint(0, len(folders))
            shutil.rmtree(oldest) #folders[i].as_posix())
            folders = list(out_path.glob('*'))
    except Exception as e: print(e)#self.logger.error(f'Error removing folders: {e}')
    
    api    = API.API[sample_config['sensor']]()
    if 'aquaverse' in global_config.ac_methods:
        run_aquaverse_download(scene_id=sample_config['scene_id'],sensor = sample_config['sensor'],AQV_location=global_config.ac_path['aquaverse'],stream_backend_path=global_config.stream_backend_path,stream_env_path=global_config.stream_env_path,output_folder=kwargs['scene_folder'],overwrite = global_config.overwrite)
        #copy tar to local repo
        run_aquaverse_pull_tar(scene_id=sample_config['scene_id'], AQV_location=global_config.ac_path['aquaverse'],output_folder=kwargs['scene_folder'],timeout=600)
        
        
    kwargs['scene_path'] = api.download_scene(**kwargs)
    kwargs.update(sample_config)
    return kwargs


        
    # while time.time() - start < timeout:
    #     print("Running Aquaverse download for:", scene_id)
    #     print(time.time() - start)
    #     "-redownload" #if overwrite
        #aquaverse_csv_filename
    
