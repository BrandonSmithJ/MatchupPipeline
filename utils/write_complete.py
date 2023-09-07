
def write_complete(scene_path,ac_method,ac_methods,out_string="",remove_scene_folder=True):
    import shutil
    import os
    print("Scene Path is: ",scene_path)
    comp_path = scene_path.parent.joinpath(ac_method)
    with open(comp_path,"w+") as complete_file:
        complete_file.write(out_string)
            
    #If all files exist, delete directory
    avail_files  = [f for f in os.listdir(scene_path.parent) if os.path.isfile(scene_path.parent.joinpath(f)) and f in ac_methods ]
    if set(avail_files) == set(ac_methods):
        if remove_scene_folder:
            shutil.rmtree(scene_path)
