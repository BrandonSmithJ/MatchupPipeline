import numpy as np
def find_nearest_lat_lon(lat_grid, lon_grid, target_lat, target_lon):
    """Find the nearest latitude and longitude in a 2D grid.
   
    Args:
            lat_grid (numpy.ndarray): 2D array of latitudes.
            lon_grid (numpy.ndarray): 2D array of longitudes.
            target_lat (float): Target latitude.
            target_lon (float): Target longitude.
   
    Returns:
            tuple: The nearest latitude and longitude values.
    """
   
    # Calculate the absolute difference between target and grid points
    lat_diff = np.abs(lat_grid - target_lat)
    lon_diff = np.abs(lon_grid - target_lon)
   
    # Calculate the combined distance using Euclidean distance
    distance = np.sqrt(lat_diff**2 + lon_diff**2)
   
    # Find the index of the minimum distance
    min_index = np.unravel_index(np.argmin(distance), distance.shape)
   
    # Return the nearest latitude and longitude
    return lat_grid[min_index], lon_grid[min_index], min_index 

