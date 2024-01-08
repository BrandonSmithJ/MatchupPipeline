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
    scenes = api.search_scenes(sensor, location, dt_range,**{'max_cloud_cover': global_config.max_cloud_cover})
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
    else:
        print('No Scenes found')
        kwargs={}

    return kwargs if global_config.timeseries_or_matchups == 'matchups' else total_kwargs

    # If there aren't any scenes found, break out of the pipeline chain
    # self.request.chain = None

def run_aquaverse_download(scene_id,sensor,output_folder,stream_backend_path,stream_env_path,AQV_location,location="Bay",timeout=1800,overwrite=False):
    import csv, os,time
    from pathlib import Path
    from subprocess import Popen, PIPE, check_output, STDOUT
    #assert(0)
    AQV_download = AQV_location+'/download_AQV'
    scene_output = str(output_folder)+'/'+scene_id +'/' 
    Path(scene_output).mkdir(parents=True,exist_ok=True)
    #Checks if the scene is already downloaded
    downloaded_file = '/tis/stream/data/' + scene_id + '.tar.gz'
    print(downloaded_file)
    if overwrite and os.path.exists(downloaded_file):
        print("Removing:",downloaded_file)
        os.remove(Path(downloaded_file))
    
    if not os.path.exists(downloaded_file) or overwrite:
        aquaverse_csv_filename = scene_output + 'aquaverse_scene.csv'
        print(aquaverse_csv_filename)
        with open(aquaverse_csv_filename, 'w', newline='') as csvfile:
            row_writer = csv.writer(csvfile, delimiter=',')
            row_writer.writerow([scene_id])
            
        #activates environment and runs download, waiting for return (timeout)
        running_procs = Popen([AQV_download, str(stream_backend_path), str(stream_env_path), str(aquaverse_csv_filename), '--redownload' ,str(sensor)], stdout=PIPE, stderr=PIPE)
        proc_coms = run_subprocess(running_procs,timeout=timeout)
        #for proc_com in proc_coms:
        #    print(proc_com)
        start = time.time()
        while not os.path.exists(downloaded_file) and time.time()-start < timeout:
            print("Waiting for output... ",downloaded_file, time.time()-start , "seconds")
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
    print('Unzipping tar file ...')
    scene_id_path = str(output_folder) + '/' + scene_id + '/'
    tar_path = scene_id_path + scene_id +'.tar.gz'
    tar = tarfile.open(tar_path)
    tf_contents = tar.getnames()
    tf_matching_scene_id_list = [file for file in tf_contents if scene_id in file]
    for file in tf_matching_scene_id_list:
        tar.extract(member=file,path=scene_id_path)
    # tar.extractall(scene_id_path)
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
    from pathlib import Path
    # Quick hack to minimize risk of running out of space
    try:
        folders = list(out_path.glob('*'))
        if (len(folders)>global_config.max_processing_scenes):
            import time
            pause_duration = 3600
            print('Length of folders is:', len(folders),' which is > the limit of:',global_config.max_processing_scenes,'. pausing for: ',pause_duration,' seconds for AC to catch up before deleting oldest files.')
            time.sleep(pause_duration)
            folders = list(out_path.glob('*'))

        while (len(folders)>global_config.max_processing_scenes):
            import numpy as np
            import shutil
            oldest = min(folders, key=lambda f: f.stat().st_ctime)#i = np.random.randint(0, len(folders))
            shutil.rmtree(oldest) #folders[i].as_posix())
            folders = list(out_path.glob('*'))
    except Exception as e: print(e)#self.logger.error(f'Error removing folders: {e}')
    
    api    = API.API[sample_config['sensor']]()
    scene_output = str(kwargs['scene_folder'])+'/'+str(sample_config['scene_id']) +'/'
    kwargs['scene_path'] = Path(scene_output)
    
    sample_config['scene_path'] = kwargs['scene_path']
    if  global_config.download_via_aquaverse:
        run_aquaverse_download(scene_id=sample_config['scene_id'],sensor = sample_config['sensor'],AQV_location=global_config.ac_path['aquaverse'],stream_backend_path=global_config.stream_backend_path,stream_env_path=global_config.stream_env_path,output_folder=kwargs['scene_folder'],overwrite = global_config.overwrite)
        #copy tar to local repo
        tis_output_path = '/tis/stream/data/'+str(kwargs['scene_id']) + '.tar.gz'
        from ..utils.decompress import decompress
        decompress(Path(tis_output_path),Path(kwargs['scene_path']),remove=False)
        #run_aquaverse_pull_tar(scene_id=sample_config['scene_id'], AQV_location=global_config.ac_path['aquaverse'],output_folder=kwargs['scene_folder'],timeout=600)
        
    #kwargs.pop('scene_path')    
    #sample_config.pop('scene_path')
    else: 
        kwargs.pop('scene_path')
        sample_config.pop('scene_path')
        kwargs['scene_path'] = api.download_scene(**kwargs)

    if 'aquaverse' in global_config.ac_methods:
        #compress output
        
        #push to stream
        from ..utils.compress import compress
        import os
        tis_output_path = '/tis/stream/data/'+str(kwargs['scene_id']) + '.tar.gz'
        if global_config.overwrite and os.path.exists(tis_output_path):
            print("Removing:",tis_output_path)
            os.remove(Path(tis_output_path))
        if not os.path.exists(tis_output_path):
            if 'OLI' == sample_config['sensor']:
                compress(tis_output_path, kwargs['scene_path'],directory_or_contents='contents')
            if 'MSI' == sample_config['sensor']:
                compress(tis_output_path,kwargs['scene_path'].joinpath(kwargs['scene_id']+'.SAFE'),directory_or_contents='directory')
            #update database
            from ..utils.insert_satellite_data import insert_satellite_data
            insert_satellite_data(sample_config['scene_id'])


    kwargs.update(sample_config)
    return kwargs


        
    # while time.time() - start < timeout:
    #     print("Running Aquaverse download for:", scene_id)
    #     print(time.time() - start)
    #     "-redownload" #if overwrite
    #t 
        #aquaverse_csv_filename
    
