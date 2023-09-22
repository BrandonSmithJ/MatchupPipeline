from pipeline.utils.search_path import split_path


def write_complete(scene_path,ac_method,ac_methods,out_string="",remove_scene_folder=True):
    import shutil
    import os
    scene_path = split_path(scene_path,split_key='Scenes',relative_location=2,required_path_content='Gathered',required_path_content_relative_location=-1)
    print("Scene Path is: ",scene_path)
    
    comp_path = scene_path.joinpath(ac_method)
    with open(comp_path,"w+") as complete_file:
        complete_file.write(out_string)
            
    #If all files exist, delete directory
    print(os.listdir(scene_path))
    avail_files  = [f for f in os.listdir(scene_path) if os.path.isfile(scene_path.joinpath(f)) and f in ac_methods ]
    if set(avail_files) == set(ac_methods):
        if remove_scene_folder:
            shutil.rmtree(scene_path)
