from shapely.geometry.base import BaseGeometry
from shapely import wkt
from typing import List, Optional, Union 



class Location:
    """Class which wraps multiple representations of a location.

    This class allows multiple representations of a location, and
    provides functions to transform them into other representations.

    """
    n = s = e = w = None
    lat = lon = None
    footprint = None


    def __init__(self, **kwargs):
        """
        A Location object should only be created with keyword arguments.
        These can be any _one_ set of
            - n, s, e, w : north/south/east/west bounding box
            - lat, lon   : point coordinate of latitude and longitude
            - footprint  : string footprint
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

        nsew   = all(getattr(self, k) is not None for k in 'nsew')
        point  = (self.lat is not None) and (self.lon is not None)
        fprint = self.footprint is not None
        assert(sum([nsew, point, fprint]) == 1), (
            'Only one of the representations should be set')

        # Create missing attributes
        if nsew:
            get_nsew   = lambda nsew_char: str( getattr(self, nsew_char) )
            fmt_corner = lambda corner: ' '.join(map(get_nsew, corner))
            fp_corners = ['wn', 'ws', 'es', 'en', 'wn']

            fp_corners_str = ', '.join(map(fmt_corner, fp_corners))
            self.footprint = wkt.loads(f'MULTIPOLYGON ((({fp_corners_str})))')

            self.lat = (self.n + self.s) / 2
            self.lon = (self.e + self.w) / 2
            self.given = 'bbox'

        if point:
            degree = 0.2 # Degree window around point
            self.n = self.lat + degree
            self.s = self.lat - degree
            self.e = self.lon + degree
            self.w = self.lon - degree
            self.footprint = wkt.loads(f'POINT ({self.lon} {self.lat})')
            self.given = 'point'

        if fprint:
            self.footprint     = wkt.loads(self.footprint)
            self.lat, self.lon = self.footprint.y, self.footprint.x
            self.w, self.s, self.e, self.n = self.footprint.bounds
            self.given = 'footprint'
            


    def __str__(self):
        string = ', '.join([f'{k}:{v}' for k, v in (
            self.get_bbox(given=True, as_dict=True) or 
            self.get_point(given=True, dict_keys=['lat', 'lon']) or 
            self.get_footprint(given=True,as_string=True, dict_key='footprint')
        ).items()])
        return f'Location({string})'



    def __repr__(self):
        return str(self)



    def get_bbox(self,
        order     : Union[str, List[str]] = 'nsew', 
        given     : bool                  = False,  
        as_dict   : bool                  = False, 
        dict_keys : Optional[List[str]]   = None,
    ) -> Union[List[float], dict]:
        """Get the bounding box for this Location.
        
        The bounding box is returned as a list of floats in the
        requested order (if as_dict=True, it's a dictionary with 
        the order as keys). 

        Parameters
        ----------
        order     : Union[str, List[str]], optional
            Order of the bounding box coordinates; e.g. 'nsew'. 
            `order` can be a list of characters, or a string which
            joins them together; i.e. ['n', 's', 'e', 'w'] == 'nsew'.
        given     : bool, optional 
            If True, return None if bbox wasn't the original representation
            that initialized this Location object.
        as_dict   : bool, optional 
            If True, return a dictionary mapping `{direction: value}`.
        dict_keys : List[str], optional
            Keys to use for the return dictionary; uses `order` if 
            None is given, but as_dict=True. `dict_keys` having any
            value besides `None` implies as_dict=True.

        Returns
        -------
        Union[List[float], dict]
            Will return a list of floats by default.
            If given=True, None will be returned if bbox is not the 
            original representation.
            If as_dict=True, a dictionary is returned rather than a 
            list, mapping direction to value (using `dict_keys` as 
            the keys if not None, and `order` otherwise).

        """
        if (not given) or (self.given == 'bbox'): 
            if isinstance(order, str):
                order = [o for o in order]

            values = [getattr(self, o) for o in order]
            if as_dict or (dict_keys is not None):
                keys = dict_keys or order
                return dict(zip(keys, values))
            return values



    def get_point(self,
        order     : List[str]           = ['lat', 'lon'],   
        given     : bool                = False,  
        as_dict   : bool                = False, 
        dict_keys : Optional[List[str]] = None, 
    ) -> Union[List[float], dict]:
        """Get the lat/lon for this Location.

        The lat/lon is returned as a list of floats in [lat, lon] order
        by default. If dict_keys is given, this function returns a dictionary
        with dict_keys representing [lat key, lon key] by default. Both of these 
        orders can be changed via the `order` keyword argument.

        Parameters
        ----------
        order     : List[str], optional
            Order of the returned list, as well as order of the `dict_keys`. 
        given     : bool, optional 
            If True, return None if point wasn't the original representation
            that initialized this Location object.
        as_dict   : bool, optional 
            If True, return a dictionary mapping `{direction: value}`.
        dict_keys : List[str], optional 
            Keys to use for the return dictionary; uses `order` if 
            None is given, but as_dict=True. `dict_keys` having any
            value besides `None` implies as_dict=True.

        Returns
        -------
        Union[List[float], dict]
            Will return a list of floats by default.
            If given=True, None will be returned if point is not the 
            original representation.
            If as_dict=True, a dictionary is returned rather than a 
            list, mapping direction to value (using `order` as the keys).

        """
        if (not given) or (self.given == 'point'): 
            values = [getattr(self, o) for o in order]
            if dict_keys is not None:
                return dict(zip(dict_keys or order, values))
            return values



    def get_footprint(self,
        given     : bool          = False, 
        as_string : bool          = False,   
        as_dict   : bool          = False, 
        dict_key  : Optional[str] = None, 
    ) -> Union[BaseGeometry, dict]:
        """
        Get the footprint for this Location, which is returned as a shapely wkt object by default. 
        If as_string=True, the wkt string representation is returned instead. 

        The lat/lon is returned as a list of floats in [lat, lon] order
        by default. If dict_keys is given, this function returns a dictionary
        with dict_keys representing [lat key, lon key] by default. Both of these 
        orders can be changed via the `order` keyword argument.

        Parameters
        ---------- 
        given     : bool, optional 
            If True, return None if footprint wasn't the original 
            representation that initialized this Location object.
        as_string : bool, optional 
            If True, return the string representation of the 
            footprint rather than the shapely object. Note that
            `as_string` and `as_dict` can both be set to True, 
            in which case a dictionary containing 
            {'footprint': `footprint string`} will be returned. 
        as_dict   : bool, optional 
            If True, return a dictionary mapping `{'footprint': value}`.
        dict_key  : str, optional 
            Key to use for the return dictionary; uses 'footprint' if 
            None is given, but as_dict=True. `dict_key` having any
            value besides `None` implies as_dict=True.

        Returns
        -------
        Union[BaseGeometry, dict]
            Will return a shapely.wkt object by default.
            If given=True, None will be returned if footprint is not the 
            original representation.
            If as_dict=True, a dictionary is returned rather than an
            object, mapping `dict_key` to value (using 'footprint' 
            if no value is passed to `dict_key`).

        """
        if (not given) or (self.given == 'footprint'): 
            value = self.footprint
            if as_string: 
                value = value.wkt
            if as_dict or (dict_key is not None):
                return {(dict_key or 'footprint') : value}
            return value

