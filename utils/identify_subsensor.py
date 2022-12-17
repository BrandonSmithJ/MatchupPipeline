
def identify_subsensor(inp_file, sensor) -> str:
   """Return the name of the output product map.

    Parameters
    ----------
    inp_file 
        Downloaded and corrected tile name
    sensor
        Input sensor
    Returns
    -------
    str
        String representation of the subsensor (if any).

    References
    ----------
    
    """
   sensor_duplicates = { 'OLCI' : ['S3A','S3B'],
                         'MSI' : ['S2A','S2B'],
                         'MOD' : ['MODA','MODT'],} 
   if sensor in sensor_duplicates.keys() :
       for sub_sensor in sensor_duplicates[sensor] :
           if sub_sensor in str(inp_file): sensor = sub_sensor
   if sensor == 'MOD': sensor = sensor+str(inp_file)[str(inp_file).find('MOD')+4] 
   
   return sensor