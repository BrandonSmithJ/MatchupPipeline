from ..Plot.plot_L2  import plot_products
from ..Plot.plot_Rrs import plot_all_Rrs as plot_Rrs
from .. import app
from argparse import Namespace

@app.task(bind=True, name='plot', queue='plot',priority=5)
def plot(self,
 	sample_config : dict,      # Config for this sample
 	global_config : Namespace, # Config for the pipeline
) -> dict:                     # Returns new sample config state
    """ Plot mapped products from the given scene """
    # if global_config.plot_products:
    sample_config['out_path'] = global_config.output_path.joinpath(*[ sample_config[k] 
                          for k in ['dataset', 'sensor', 'ac_method']])
    def parse_date(input_str):
        sid = str(sample_config['inp_file']).split('/')[-1]
        if sample_config['sensor']=='MERIS':
            return sid.split('_')[5].split('T')[0] 
        if sample_config['sensor'] == 'MOD':
            return sid[1:]
        if sample_config['sensor'] in ['S3A','S3B','OLCI']:
            return sid.split('____')[1].split('_')[0] 
        if sample_config['sensor'] in ['OLI']:
            return sid.split('_')[3]
        if sample_config['sensor'] in ['MSI']:
            return sid.split('_')[-1].split('T')[0]
        return     sid.split('.')[1]
        
    kwargs = {
    	'sensor'   : sample_config['sensor'],
    	'inp_file' : sample_config['correction_path'],
        'out_path' : sample_config['out_path'],
        'overwrite': global_config.overwrite,
        'dataset'  : sample_config['dataset'],
        'date'     : parse_date(sample_config['inp_file']),
        'ac_method': sample_config['ac_method'],
        'fix_projection_Rrs': global_config.fix_projection_Rrs,
     	}
    if global_config.plot_products: plot_products(**kwargs)
    if global_config.plot_Rrs:     
        # OLI
        #sensor = 
        #base_dir = '/data/roshea/SCRATCH/Gathered/Scenes/OLI/LC08_L1TP_044034_20200708_20200912_02_T1/out/OLI_test_image_san_fran_XCI0001/'
        #scene_id = 'LC08_L1TP_044034_20200708_20200912_02_T1'
        
        kwargs_Rrs = {
            'base_dir' : str(kwargs['inp_file'].parent),
            'scene_id' : str(kwargs['inp_file'].parent.parent.parent.stem),
            'out_path' : str(sample_config['out_path'].parent.joinpath('Rrs_maps')),
            'sensor'   : sample_config['sensor'],
            'atm_corrs': ['acolite','l2gen','polymer']
            }
        #MSI
        # base_dir = '/data/roshea/SCRATCH/Gathered/Scenes/MSI/S2A_MSIL1C_20201017T155251_N0209_R054_T18SUH_20201017T193914/out/MSI_test_image_20201017_XCI0001/'
        # scene_id = 'S2A_MSIL1C_20201017T155251_N0209_R054_T18SUH_20201017T193914'

        # atm_corrs = ['acolite','l2gen','polymer']
        # sensor='MSI'
        if kwargs_Rrs['sensor'] in ['MSI','OLI']:
            plot_Rrs(**kwargs_Rrs)
        # plot_Rrs(base_dir, scene_id, atm_corrs= ['acolite','l2gen','polymer'], sensor='OLI')
        
    kwargs.update(sample_config)
    return kwargs

 