import numpy as np
from pipeline.utils.identify_subsensor import identify_subsensor
from pathlib import Path

def product_name(inp_file, out_path,date,dataset,sensor,ac_method,product,extension,prefix='AQV') -> str:
   """Return the name of the output product map.

    Parameters
    ----------
    product : Chl,tss,cdom,PC, etc.
        Product(s) being plotted. 
    
    date : YYYYMMDD,
        Date of atellite imagery

    time : HHMMSS,
        Time of satellite overpass

    location : SaltonSea
        Location of satellite imagery 

    extension : .nc
        Filetype extension

    Returns
    -------
    str
        String representation of the product's name in the code.

    References
    ----------
    
    """
   sensor = identify_subsensor(inp_file,sensor)
   date=date.strftime("%Y_%m_%d")
   product='_'.join((product.split(',')))
   product_name = '_'.join([prefix,date,dataset,sensor,ac_method,product+extension])
   extension_folder = extension.split('.')[-1]+'s'
   out_path = Path(out_path).joinpath(extension_folder)
   out_path.mkdir(exist_ok=True, parents=True)
   
   return f'{out_path}/{product_name}'


