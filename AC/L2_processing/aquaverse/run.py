from pathlib import Path

import numpy as np
import tempfile, sys
import shutil
from typing import Union, Optional


try: 
    from ....utils import Location, assert_contains
    from ....utils.run_subprocess import run_subprocess
    from ....exceptions import MissingProcessorError, AtmosphericCorrectionError


except: 
    sys.path.append(Path(__file__).parent.parent.parent.as_posix())
    sys.path.append(Path(__file__).parent.parent.parent.parent.as_posix())
    from utils import Location, assert_contains
    from utils.run_subprocess import run_subprocess
    from exceptions import MissingProcessorError, AtmosphericCorrectionError
    

# Sensors that aquaverse can process 
VALID = [
    'MSI', 
    'OLI', 
]

def run_aquaverse_pull_tar(scene_id,output_folder,timeout=600,stream_output_path = '/tis/stream/data/'):
    from subprocess import Popen, PIPE, check_output, STDOUT
    from pathlib import Path
    import shutil
    for suffix in ['_rrs','_rayleigh_processed','']:
        downloaded_rrs = stream_output_path + scene_id + f'{suffix}.tar.gz'
        output_rrs     = output_folder + '/'+ scene_id + f'{suffix}.tar.gz'
        shutil.copyfile(downloaded_rrs, output_rrs)
        
        # finds and unpacks tar
        import tarfile
        print('Unzipping tar file ...',suffix)
        tar = tarfile.open(output_rrs)
        tf_contents = tar.getnames()
        tf_matching_scene_id_list = [file for file in tf_contents if scene_id in file]
        for file in tf_matching_scene_id_list:
            tar.extract(member=file,path=output_folder)
        # tar.extractall(output_folder)
        tar.close()

import psycopg2
def check_ancillary_present(date):
    sql = f"SELECT * FROM ancillary_data WHERE creation_date = '{date}';"      
    conn = None
    try:
        conn = psycopg2.connect(service='stream-stage-rw')
        cur = conn.cursor()
        cur.execute(sql, ())
        results = cur.fetchall()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise
    finally:
        if conn is not None:
            conn.close()

    return(len(results))    
    
def run_aquaverse_ancillary(sensor,scene_id, AQV_location,timeout=600,stream_backend_path='/tis/m2cross/scratch/f002/wwainwr1/stream/backend', stream_env_path='/tis/m2cross/scratch/f002/wwainwr1/venv/bin/activate'):
    from subprocess import Popen, PIPE, check_output, STDOUT
    from pathlib import Path
    # from datetime import datetime
    import datetime
    if sensor == 'OLI':
        date = scene_id.split('_')[3]
    if sensor == 'MSI':
        date = scene_id.split('_')[2].split('T')[0]
    date_out = datetime.datetime.strptime(date,'%Y%m%d')
    date_out_start = date_out.strftime('%Y-%m-%d')
    date_out_end   = date_out + datetime.timedelta(days=1)
    date_out_end   = date_out_end.strftime('%Y-%m-%d')
    # year  = scene_id.split('_')[2].split('T')[0][0:4]
    # month = scene_id.split('_')[2].split('T')[0][4:6]
    AQV_pull_tar = str(AQV_location)+'/ancillary_AQV'
    len_available_ancillary_files = check_ancillary_present(date_out_start)
    #if len_available_ancillary_files > 2:
    print(AQV_pull_tar,date_out_start,date_out_end)
    running_procs = Popen([AQV_pull_tar, str(stream_backend_path), str(stream_env_path), str(date_out_start), str(date_out_end) ], stdout=PIPE, stderr=PIPE)
    run_subprocess(running_procs,timeout=timeout)   


    

def run_aquaverse_rayleigh(scene_id, AQV_location,timeout=3600,stream_backend_path='/tis/m2cross/scratch/f002/wwainwr1/stream/backend', stream_env_path='/tis/m2cross/scratch/f002/wwainwr1/venv/bin/activate', stream_output_path = '/tis/stream/data/',overwrite=False):
    from subprocess import Popen, PIPE, check_output, STDOUT
    from pathlib import Path
    import os
    AQV_pull_tar = str(AQV_location)+'/rayleigh_correct_AQV'
    rayleigh_output_path = stream_output_path + f'{scene_id}_rayleigh_processed.tar.gz'
    if overwrite and os.path.exists(rayleigh_output_path):
        print("Removing:",rayleigh_output_path)
        os.remove(Path(rayleigh_output_path))
    
    if not os.path.exists(rayleigh_output_path) or overwrite:
        running_procs = Popen([AQV_pull_tar, str(stream_backend_path), str(stream_env_path), str(scene_id) ], stdout=PIPE, stderr=PIPE)
        run_subprocess(running_procs,timeout=timeout)
    #Check for file and hold until complete
    import time
    start = time.time()
    file_not_found=True
    time_difference = time.time() - start 
    while time_difference < timeout and file_not_found:
        if os.path.exists(rayleigh_output_path):
            file_not_found = False
            print(rayleigh_output_path, "found after",time_difference)
            return
        else:
            print(rayleigh_output_path, "NOT found after",time_difference)
            time.sleep(30)
        time_difference = time.time() - start 
    print("Failed to find output")
            
        
    
def run_aquaverse_MDN_AC(scene_id, AQV_location,timeout=3600,stream_backend_path='/tis/m2cross/scratch/f002/wwainwr1/stream/backend', stream_env_path='/tis/m2cross/scratch/f002/wwainwr1/venv/bin/activate', stream_output_path = '/tis/stream/data/',overwrite=False):
    from subprocess import Popen, PIPE, check_output, STDOUT
    from pathlib import Path
    import os
    #Waits for Rayleigh corrected data to become available
    AQV_pull_tar = str(AQV_location)+'/MDN_AC_AQV'
    rrs_output_path = stream_output_path + f'{scene_id}_rrs.tar.gz'
    if overwrite and os.path.exists(rrs_output_path):
        print("Removing:",rrs_output_path)
        os.remove(Path(rrs_output_path))
        
    if not os.path.exists(rrs_output_path) or overwrite:
        running_procs = Popen([AQV_pull_tar, str(stream_backend_path), str(stream_env_path), str(scene_id) ], stdout=PIPE, stderr=PIPE)
        run_subprocess(running_procs,timeout=timeout)
    #Waits for MDN-AC corrected data to become available
    #Check for file and hold until complete
    import time
    start = time.time()
    file_not_found=True
    time_difference = time.time() - start 
    while time_difference < timeout and file_not_found:
        if os.path.exists(rrs_output_path):
            file_not_found = False
            print(rrs_output_path, "found after", time_difference)
            return
        else:
            
            print(rrs_output_path, "NOT found after", time_difference)
            time.sleep(30)
        time_difference = time.time() - start 
    print("Failed to find output")
            
    
# @subprocess_wrapper
def run_aquaverse(
    sensor    : str,
    inp_file  : Union[str, Path],
    out_dir   : Union[str, Path],
    ac_path   : Union[str, Path]   = '',
    overwrite : bool               = False, 
    timeout   : float              = 30, 
    location  : Optional[Location] = None, 
    **extra_cmd, 
) -> Path:
    """Atmospherically correct the given input file using aquaverse.

    Parameters
    ----------
    sensor    : str
        Satellite sensor (e.g. OLI, MSI).
    inp_file  : Path, str
        Path to the L1 input file to atmospherically correct.
    out_dir   : Path, str
        Directory to write the L2 result to.
    ac_path   :Path, str, optional
        Aquaverse installation directory. Must be given if atmospheric correction
        is actually being performed (i.e. the L2 file doesn't already exist).
    overwrite : bool, optional
        Overwrite the L2 output file if it already exists.
    timeout   : float, optional
        Number of minutes acolite is allowed to run before a TimeoutError 
        is raised.
    location  : Location, optional
        Location object which defines a bounding box to perform atmospheric
        correction on. Allows much faster processing if only a small area of
        the L2 output is actually required. 
    **extra_cmd
        Additional keywords that can be passed to this function are:
            * Any other acolite parameters.

    Returns
    -------
    Path
        Path to the L2 output file (i.e. `out_dir`/aquavers.TIF). 

    Raises
    ------
    TimeoutError
        If execution of any subprocess takes longer than `timeout` minutes.
    InvalidSelectionError
        If an invalid sensor is given as input, or credentials are missing
        for urs.earthdata.nasa.gov.
    MissingProcessorError
        If the aquaverse installation is not found.
    AtmosphericCorrectionError
        If aquaverse fails for any reason; check the error message for reason.

    References
    ----------

    """
    assert_contains(VALID, sensor, 'aquaverse sensor')

    # Setup paths
    inp_file = Path(inp_file).absolute()
    if sensor in ['MSI']: inp_file = Path(inp_file).joinpath(str(inp_file.stem) + '.SAFE')
    out_file = Path(out_dir).absolute().joinpath('aquaverse.TIF')
    outputs = list(out_file.parent.glob('*RRS*nm.TIF'))
    # Only run if output doesn't yet exist, or we want to overwrite
    if not len(outputs) or overwrite or True:
            
        # Add the acolite installation to the working path, and import acolite
        ac_path = Path(ac_path)
        if not ac_path.exists():
            message = f'Aquaverse installation does not exist at "{ac_path}"'
            raise MissingProcessorError(message)
        sys.path.append(ac_path.parent.as_posix())
        settings = {
            'inputfile'      : inp_file.as_posix(),
            # 'output'         : out_file.parent.as_posix(),
            'l2w_parameters' : 'Rrs_*',
            'verbosity'      : 2,
        }
        
        # Run aquaverse raleigh correction
        scene_id_location = -2 if sensor == 'MSI' else-1
        scene_id = settings['inputfile'].split('/')[scene_id_location]
        print("Running Aquaverse Rayleigh ancillary data...")
        run_aquaverse_ancillary(sensor,scene_id, ac_path,timeout=timeout*60)
        print("Running Aquaverse Rayleigh correction...")
        run_aquaverse_rayleigh(scene_id, ac_path,timeout=timeout*60,overwrite = overwrite)
        print("Running Aquaverse Rrs correction...")
        # Run aquaverse correction
        run_aquaverse_MDN_AC(scene_id, ac_path,timeout=timeout*60,overwrite = overwrite)
        
        run_aquaverse_pull_tar(scene_id, out_file.parent.as_posix(),timeout=int(timeout*60/10),stream_output_path = '/tis/stream/data/')
        
        # Ensure the expected file exists
        outputs = list(out_file.parent.glob('*RRS*nm.TIF'))
        if len(outputs) <= 1:
            msg = f'Aquaverse failure. Output directory contents: {outputs}'
            if 'Scenes' in settings['inputfile'] and sensor in settings['inputfile'] and False:
                shutil.rmtree(settings['inputfile'])
            raise AtmosphericCorrectionError(msg)

        # Delete previous output file if it exists
        # if out_file.exists(): out_file.unlink()
        # from osgeo import gdal
        # inputfile = str(outputs[0])
        # input_file_lat_lon = str(outputs[0].parent.joinpath('aquaverse_tif_lat_lon.tif'))
        # outputfile = str(outputs[0].parent.joinpath('aquaverse_lat_lon.nc'))
        # ds = gdal.Translate(str(outputfile), str(input_file_lat_lon), format='NetCDF')
        # ds = gdal.Warp(input_file_lat_lon, inputfile, dstSRS="+proj=longlat +datum=WGS84 +no_defs")
        
        # from osgeo import gdal, osr
        # ds = gdal.Open(inputfile)
        # width = ds.RasterXSize
        # height = ds.RasterYSize
        # gt = ds.GetGeoTransform()
        # minx = gt[0]
        # miny = gt[3] + width*gt[4] + height*gt[5] 
        # maxx = gt[0] + width*gt[1] + height*gt[2]
        # maxy = gt[3] 
# #         wgs84_wkt = """GEOGCRS["WGS 84",
# #     DATUM["World Geodetic System 1984",
# #         ELLIPSOID["WGS 84",6378137,298.257223563,
# #             LENGTHUNIT["metre",1]]],
# #     PRIMEM["Greenwich",0,
# #         ANGLEUNIT["degree",0.0174532925199433]],
# #     CS[ellipsoidal,2],
# #         AXIS["geodetic latitude (Lat)",north,
# #             ORDER[1],
# #             ANGLEUNIT["degree",0.0174532925199433]],
# #         AXIS["geodetic longitude (Lon)",east,
# #             ORDER[2],
# #             ANGLEUNIT["degree",0.0174532925199433]],
# #     ID["EPSG",4326]]
# # """
#         wgs84_wkt = """"
#         GEOGCS["WGS 84",
#             DATUM["WGS_1984",
#                 SPHEROID["WGS 84",6378137,298.257223563,
#                     AUTHORITY["EPSG","7030"]],
#                 AUTHORITY["EPSG","6326"]],
#             PRIMEM["Greenwich",0,
#                 AUTHORITY["EPSG","8901"]],
#             UNIT["degree",0.01745329251994328,
#                 AUTHORITY["EPSG","9122"]],
#             AUTHORITY["EPSG","4326"]]"""
#         new_cs = osr.SpatialReference()
#         new_cs .ImportFromWkt(wgs84_wkt)
#         old_cs= osr.SpatialReference()
#         old_cs.ImportFromWkt(ds.GetProjectionRef())
        # transform = osr.CoordinateTransformation(old_cs,new_cs) 

        # def getCoords(r,c,transform):
        #     posX = transform.px_w * c + transform.rot1 * r + transform.xoffset + transform.px_w / 2
        #     posY = transform.rot2 * c + transform.px_h * r + transform.yoffset + transform.px_h / 2
        #     lat,long,z = transform.image_transform.TransformPoint(posX,posY)
        # zip(*[getCoords(r,c,transform) for r,c in zip([0,height,0,height],[0,0,width,width])])

#         import rioxarray
# # 
#         rds = rioxarray.open_rasterio(inputfile)
#         rds_4326 = rds.rio.reproject("EPSG:4326")
#         rds_4326.rio.to_raster(input_file_lat_lon)
#         rds_4326.rio.to_raster(input_file_lat_lon, compress="DEFLATE", tiled=True)

    return out_file         



if __name__ == '__main__':
    folder = '/scratch/job/14121763/Tiles/OLI/20180809/LC08_L1TP_015034_20180809_20180815_01_T1'
    folder = 'D:/Plotting/Simultaneous/Matchup_Pipeline/workspace/SCRATCH/Gathered/Scenes/ETM/LE07_L1TP_007027_20200627_20200824_01_T1/LE07_L1TP_007027_20200627_20200824_01_T1_MTL.txt'
    output = Path(folder).parent.joinpath('out').as_posix()

