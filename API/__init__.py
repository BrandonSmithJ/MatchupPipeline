from .ETM   import ETM
from .HICO  import HICO 
from .MERIS import MERIS 
from .MOD   import MOD
from .MSI   import MSI
from .OCI   import OCI
from .EMIT  import EMIT
from .OLCI  import OLCI 
from .OLI   import OLI 
from .TM    import TM 
from .VI    import VI 


# Dictionary mapping sensor to the respective search/download API 
# object used for that sensor
API = {
	# Landsat
	'TM'    : TM,
	'ETM'   : ETM,
	'OLI'   : OLI,
	
	# Sentinel
	'MSI'   : MSI,
	'OLCI'  : OLCI,

	# Others
	'HICO'  : HICO,
	'MERIS' : MERIS,
	'MOD'   : MOD,
	'VI'    : VI,
        'OCI'   : OCI,
        'EMIT'  : EMIT,
}
