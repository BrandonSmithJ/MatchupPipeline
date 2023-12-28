from ..AC.L2_processing import AC_FUNCTIONS
from .. import app
from argparse import Namespace
from ..utils.convert_tif_nc import convert_tif_nc

@app.task(bind=True, name='correct', queue='correct', priority=2, max_retries=0)
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
        'overwrite' : global_config.overwrite, # Correcting only for small area needs overwrite
        'timeout'   : global_config.ac_timeout,
        'location'  : sample_config['location'],
    }
    kwargs.update(global_config.extra_cmd[ac_method][sample_config['sensor']] if ac_method in global_config.extra_cmd.keys() and sample_config['sensor'] in global_config.extra_cmd[ac_method].keys() else {})
    if not global_config.apply_bounding_box: kwargs['location'] = None
    if ac_method == 'aquaverse': kwargs.update({'prod_level': global_config.aquaverse_prod_level})
    kwargs['correction_path'] = AC_FUNCTIONS[ac_method](**kwargs)
    if ac_method == 'aquaverse': kwargs['correction_path']  = convert_tif_nc(str(out_path)+'/')
    if global_config.remove_L1_tile: 
        for L1A_path in list(inp_path.glob('**/*.L1A*')):
            L1A_path.unlink()
        for GEO_path in list(inp_path.glob('**/*.GEO*')):
            GEO_path.unlink()
        for L1B_path in list(inp_path.glob('**/*.L1B*')):
            L1B_path.unlink()
    kwargs.update(sample_config)
    kwargs.update({'ac_method': ac_method})

    return kwargs
