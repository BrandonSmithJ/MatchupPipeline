from .l2gen.run     import run_l2gen
from .polymer.run   import run_polymer
from .acolite.run   import run_acolite
from .aquaverse.run import run_aquaverse

# Dictionary mapping the available AC methods to the
# respective names of the AC program
AC_FUNCTIONS = {
	'l2gen'    : run_l2gen,
	'polymer'  : run_polymer,
	'acolite'  : run_acolite,
    'aquaverse': run_aquaverse,
}
