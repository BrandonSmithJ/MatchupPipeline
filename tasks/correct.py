from ..AC.L2_processing import AC_FUNCTIONS
from .. import app
from argparse import Namespace


@app.task(bind=True, name='correct', queue='correct', priority=2)
def correct(self,
    sample_config : dict,      # Config for this sample
    ac_method     : str,       # AC method to use for correction
    global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
    """ Atmospherically correct the given scene """
    inp_path = (sample_config['scene_path']
             if sample_config['scene_path'].exists() else 
                sample_config['scene_path'].parent)
    out_path = (inp_path if inp_path.is_dir() else 
                inp_path.parent).joinpath('out', sample_config['uid'])
    out_path.mkdir(exist_ok=True, parents=True)

    kwargs = {
        'sensor'    : sample_config['sensor'],
        'inp_file'  : inp_path,
        'out_dir'   : out_path,
        'ac_path'   : global_config.ac_path[ac_method],
        'overwrite' : True, # Correcting only for small area needs overwrite
        'timeout'   : global_config.ac_timeout,
        'location'  : sample_config['location'],
    }
    kwargs['correction_path'] = AC_FUNCTIONS[ac_method](**kwargs)
    kwargs.update(sample_config)
    kwargs.update({'ac_method': ac_method})
    return kwargs
