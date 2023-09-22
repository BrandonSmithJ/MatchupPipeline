from pathlib import Path
def split_path(scene_path,split_key='Scenes',relative_location=0,required_path_content='',required_path_content_relative_location=-1):
    split_scene_path  = str(scene_path).split('/')
    scene_location    = [i for i,split_path in enumerate(split_scene_path) if split_path =='Scenes'][0]
    output_scene_path = Path(('/').join(split_scene_path[0:1+scene_location+relative_location]))
    if required_path_content in split_scene_path[scene_location+required_path_content_relative_location]:
        return output_scene_path
    else:
        assert(0)
        return scene_path
