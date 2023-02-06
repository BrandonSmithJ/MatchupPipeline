from ..Plot.plot_L2 import plot_products
from .. import app
from argparse import Namespace

@app.task(bind=True, name='plot', queue='plot')
def plot(self,
 	sample_config : dict,      # Config for this sample
 	global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
    """ Plot mapped products from the given scene """
    sample_config['out_path'] = global_config.output_path.joinpath(*[ sample_config[k] 
                          for k in ['dataset', 'sensor', 'ac_method']])
    
    kwargs = {
		'sensor'   : sample_config['sensor'],
		'inp_file' : sample_config['correction_path'],
        'out_path' : sample_config['out_path'],
        'overwrite': global_config.overwrite,
        'dataset'  : sample_config['dataset'],
        'date'     : str(sample_config['inp_file']).split('/')[-1][1:] if sample_config['sensor'] == 'MOD' else str(sample_config['inp_file']).split('/')[-1].split('.')[1],
        'ac_method': sample_config['ac_method'],
        'fix_projection_Rrs': global_config.fix_projection_Rrs,
 	}
    plot_products(**kwargs)
    kwargs.update(sample_config)
    return kwargs
 