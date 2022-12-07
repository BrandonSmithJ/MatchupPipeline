from ..extract import extract_window
from .. import app
from argparse import Namespace


@app.task(bind=True, name='extract', queue='extract')
def extract(self,
	sample_config : dict,      # Config for this sample
	global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
	""" Extract a geolocated window from the given scene """
	
	kwargs = {
		'sensor'   : sample_config['sensor'],
		'inp_file' : sample_config['correction_path'],
		'lat'      : sample_config['lat'],
		'lon'      : sample_config['lon'],
		'window'   : global_config.extract_window,
	}
	kwargs['extracted'] = extract_window(**kwargs)
	kwargs.update(sample_config)
	return kwargs
