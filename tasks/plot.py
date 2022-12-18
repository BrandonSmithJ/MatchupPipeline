from ..Plot.plot_L2 import plot_products
from .. import app
from argparse import Namespace


@app.task(bind=True, name='map', queue='map')
def plot(self,
	sample_config : dict,      # Config for this sample
	global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
	""" Plot mapped products from the given scene """
	sample_config['out_path'] = global_config.output_path.joinpath(*[ sample_config[k] 
                          for k in ['dataset', 'sensor', 'ac_method']])
# 	sample_config['output_path_full'] = out_path
	kwargs = {
		'sensor'   : sample_config['sensor'],
		'inp_file' : sample_config['correction_path'],
        'out_path' : sample_config['out_path'],
        'overwrite': global_config.overwrite,
        'dataset'  : sample_config['dataset'],
        'date'     : sample_config['date'],
        'ac_method': sample_config['ac_method'],
	}
	plot_products(**kwargs)
	kwargs.update(sample_config)
	return kwargs
