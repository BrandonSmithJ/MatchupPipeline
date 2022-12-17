from ..atm_utils import execute_cmd

from pathlib import Path
from typing import Union, Callable, Iterable
from functools import wraps

import os, sys, subprocess, tempfile, logging


logger = logging.getLogger('MatchupPipeline')


def _run_seadas_script(script_file: str):
	''' 
	Decorator which provides a generalized way to execute SeaDAS scripts
	script_file is the .py SeaDAS script that the decorated function should execute
	'''

	def decorator(script_function: Callable) -> Callable:


		@wraps(script_function)
		def wrapper(
			inp_file  : Union[str, Path],         # Path to the L0 input file 
			ac_path   : Union[str, Path] = '',    # SeaDAS installation directory 
			overwrite : bool             = False, # Overwrite the output file if it already exists
            n         : str = '',                 # North coordinate for extract L1A
            s         : str = '',                 # South coordinate for extract L1A
            e         : str = '',                 # East coordinate for extract L1A            
            w         : str = '',                 # West coordinate for extract L1
            geofile   : str = None,               # Geofile path for L2B
		) -> None:                                # No return value
			''' 
			Wrapper function which is actually executed when calling the original script function
			'''

			# Setup paths
			inp_file    = Path(inp_file).absolute()
			out_file    = script_function(inp_file)
			ocssw_path  = Path(ac_path or 'SeaDAS').absolute()
			curr_path   = Path(__file__).parent.parent.joinpath('L2_processing','l2gen').absolute() #Path(__file__).parent.absolute()
			module_path = curr_path.joinpath('Seadas_scripts', 'modules')
			nonlocal script_file
			script_file = curr_path.joinpath('Seadas_scripts', script_file)
			ancill_path = curr_path.joinpath('Ancillary')
			ancill_path.mkdir(parents=True, exist_ok=True)

			# Only run if output doesn't yet exist, or we want to overwrite
			if not out_file.exists() or overwrite:

				# Ensure necessary locations exist
				assert(ocssw_path.exists()),  f'SeaDAS installation does not exist at "{ocssw_path}"'
				assert(script_file.exists()), f'SeaDAS script does not exist at "{script_file}"'
				assert(inp_file.exists()),    f'Input file does not exist at "{inp_file}"'

				# Create command and execution environment
				cmd = [sys.executable, script_file.as_posix(), inp_file.as_posix(), '-o', out_file.as_posix(), '--verbose']
                #Overwrite command 
				if n!='' and s!='' and e!='' and w!='':
								cmd = [sys.executable, script_file.as_posix(), inp_file.as_posix(),'-g', inp_file.as_posix().split('.')[0] + '.GEO', '-o', out_file.as_posix(),'-n',n,'-s',s,'-e',e,'-w',w, '--verbose']
				if geofile:
								cmd = [sys.executable, script_file.as_posix(), inp_file.as_posix(), geofile, '-o', out_file.as_posix(), '--verbose']
				env = dict(os.environ)
				env.update({
					'PYTHONPATH' : module_path.as_posix(),
					'L2GEN_ANC'  : ancill_path.as_posix(),
					'OCSSWROOT'  : ocssw_path.as_posix(),
					'OCVARROOT'  : ocssw_path.joinpath('var').as_posix(),
					'OCSSW_BIN'  : ocssw_path.joinpath('bin').as_posix(),
					'OCDATAROOT' : ocssw_path.joinpath('share').as_posix(),
					'LIB3_BIN'   : ocssw_path.joinpath('opt', 'bin').as_posix(),
				})

				# Execute the script in a temporary folder to ensure everything is cleaned up
				with tempfile.TemporaryDirectory(dir=inp_file.parent) as tmpdir:
					execute_cmd(cmd, env, str(tmpdir))
		return wrapper
	return decorator



@_run_seadas_script('modis_GEO.py')
def run_geo_modis(inp_file: Path) -> Path:
	''' 
	Runs Seadas_scripts/modis_GEO.py to produce MODIS GEO files for the given input
	'''
	return Path(inp_file.as_posix().replace('L1A_LAC', 'GEO'))


@_run_seadas_script('modis_L1A_extract.py')
def run_extract_modis(inp_file: Path) -> Path:
	''' 
	Runs Seadas_scripts/L1A extract.py to produce extracted MODIS files for the given input
	'''
	return Path(inp_file.as_posix().replace('L1A_LAC', 'SUB.L1A_LAC'))

@_run_seadas_script('modis_L1B.py')
def run_l1b(inp_file: Path) -> Path:
	''' 
	Runs Seadas_scripts/modis_L1B.py to produce MODIS L1B files from the given L1A input
	'''
	return Path(inp_file.as_posix().replace('L1A_LAC', 'L1B_LAC'))



def run_angles(
	inp_file  : Union[str, Path],         # Path to the angles file 
	overwrite : bool             = False, # Overwrite the output file if it already exists
) -> None:
	'''
	Generate Landsat-8 angle files
	'''

	# Setup paths
	inp_file  = Path(inp_file).absolute()
	out_file  = Path(inp_file.as_posix().replace('ANG.txt', 'sensor_B01.img'))
	curr_path = Path(__file__).parent.absolute()
	exec_path = curr_path.joinpath('l8_angles', 'l8_angles')

	# Only run if output doesn't yet exist, or we want to overwrite
	if not out_file.exists() or overwrite:

		# Ensure necessary locations exist		
		assert(exec_path.exists()), f'l8_angles program does not exist at "{exec_path}"'
		assert(inp_file.exists()),  f'Input file does not exist at "{inp_file}"'

		# Create the command and execute it
		cmd = [exec_path.as_posix(), inp_file.as_posix(), 'BOTH', '1', '-b', '1']
		execute_cmd(cmd, cwd=inp_file.parent.as_posix())



# def run_l1c(filename, output, sensor, overwrite=False, root=''):
# 	assert(root), 'Must provide seadas root directory'

# 	# cmd  = f'OCDATAROOT={root}/share OCVARROOT={root}/seadas-7.5.3/ocssw/var {root}/bin/l2gen --land=/media/brandon/NASA/SeaDAS/share/common/landmask_null.dat --oformat="netcdf4" --l2prod="rhot_nnn rhos_nnn polcor_nnn sena senz sola solz latitude longitude"'
# 	cmd  = [f'{root}/bin/l2gen', '--land=/media/brandon/NASA/SeaDAS/share/common/landmask_null.dat', '--oformat="netcdf4"', '--l2prod="rhot_nnn rhos_nnn polcor_nnn sena senz sola solz latitude longitude"']

# 	if 'MOD' in sensor or 'VI' in sensor:
# 		cmd += f' --geofile={".".join(filename.split(".")[:-1])}.GEO'

# 	output = f'{output}/l1c.nc'
# 	if not os.path.exists(output) or overwrite:
# 		cmd += [f'--ifile={filename}',f'--ofile={output}']
# 		env = dict(os.environ)
# 		env['OCDATAROOT'] = f'{root}/share'
# 		env['OCVARROOT']  = f'{root}/seadas-7.5.3/ocssw/var'
# 		process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 		_, err  = process.communicate()

# 		if process.returncode != 0:
			
# 			err = err.decode('utf-8')
# 			if 'can not read scanlines from a tiled image' in err.lower():

# 				print('Image is in tiled format - using gdalwarp to create new files.')
# 				filename = Path(filename)
# 				for tif in filename.parent.glob('*.TIF'):
# 					dst  = tif.parent.joinpath('conv', tif.name)
# 					# conv = ['tiffcp','-c','none', '-s', tif.as_posix(), dst.as_posix()]
# 					conv = ['gdalwarp','-co','TILED=NO', '-co', 'COMPRESS=DEFLATE', tif.as_posix(), dst.as_posix()]

# 					if not dst.exists():
# 						dst.parent.mkdir(parents=True, exist_ok=True)
# 						process = subprocess.Popen(conv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 						out, err= process.communicate()

# 				for txt in filename.parent.glob('*.txt'):
# 					dst = txt.parent.joinpath('conv', txt.name)
# 					if not dst.exists():
# 						shutil.copyfile(txt.as_posix(), dst.as_posix())

# 				old_inp = Path(cmd[-2].split('=')[-1])
# 				new_inp = old_inp.parent.joinpath('conv', old_inp.name).as_posix()
# 				cmd[-2] = f'--ifile={new_inp}'
# 				process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 				_, err  = process.communicate()
# 			else:
# 				raise Exception(err)
#	return output



if __name__ == '__main__':
	'''PYTHONPATH=Seadas_scripts/modules LIB3_BIN=/media/brandon/NASA/SeaDAS/opt/bin OCVARROOT=/media/brandon/NASA/SeaDAS/var OCSSW_BIN=/media/brandon/NASA/SeaDAS/bin OCSSWROOT=/media/brandon/NASA/SeaDAS OCDATAROOT=/media/brandon/NASA/SeaDAS/share python3 Seadas_scripts/modis_GEO.py /media/brandon/NASA/Plotting/Simultaneous/Insitu/Long_Island/Tiles/MOD/20100209/A2010040174000/A2010040174000.L1A_LAC --log
	'''
	run_geo_modis('/media/brandon/NASA/Plotting/Simultaneous/Insitu/Long_Island/Tiles/MOD/20100209/A2010040174000/A2010040174000.L1A_LAC', overwrite=True, root='/media/brandon/NASA/SeaDAS')
