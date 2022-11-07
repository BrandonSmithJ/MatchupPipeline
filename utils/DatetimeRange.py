from datetime import datetime as dt, timedelta as td
from dateutil import parser
from typing import List, Optional, Union 
import datetime



class DatetimeRange:
    """Class which encapsulates idea of a range of datetimes.

    This class allows multiple representations of a datetime range, and
    provides functions to transform them into other representations.

    """
    start  = end    = None 
    center = window = None


    def __init__(self, **kwargs):
        """
        A DatetimeRange object should only be created with keyword arguments.
        These can be any _one_ set of
            - start, end     : start and end date(time)
            - center, window : center date(time) and timedelta surrounding it
        """
        for k, v in kwargs.items():
            setattr(self, k, self._fmt(k, v))

        se = (self.start  is not None) and (self.end    is not None)
        cw = (self.center is not None) and (self.window is not None)
        assert((se+cw) == 1), 'Only one of the representations should be set'

        # Generate the start/end datetimes from the center/window values
        if cw: 
            self.start = self.center - self.window
            self.end   = self.center + self.window



    def __str__(self):
        if self.distance.total_seconds() < (24 * 60 * 60):
            start  = self.start.strftime('%Y%m%d %H:%M')
            string = f'{start} -> ' + self.end.strftime('%H:%M')
        else:
            string = ' -> '.join(self.strftime('%Y%m%d'))
        return f'DatetimeRange({string})'



    def __repr__(self):
        return str(self)



    def _fmt(self, k, v):
        """ Ensure values are their proper types """
        if k in ['start', 'end', 'center']:
            if isinstance(v, str):
                return parser.parse(v)
            if isinstance(v, datetime.date):
                return dt.combine(v, datetime.time.min)
            if isinstance(v, datetime.datetime):
                return v
            raise Exception(f'Invalid type for key {k}: {type(v)}')
        if k in ['window']:
            if isinstance(v, int):
                return td(days=v)
            assert(isinstance(v, td)), f'Invalid type for key {k}: {type(v)}'
        return v



    def strftime(self,
        fmt       : Optional[str]       = None,  
        as_dict   : bool                = False,
        dict_keys : Optional[List[str]] = None, 
    ) -> Union[tuple, dict]:
        """Return the start/end datetimes as strings formatted as requested.
        
        Parameters
        ----------
        fmt : str, optional
            String format to represent the datetime. If no fmt is passed, 
            the datetime objects are returned.
        as_dict   : bool, optional 
            If True, return a dictionary mapping.
        dict_keys : List[str], optional
            Keys to use for the return dictionary; uses ['start', 'end'] if 
            None is given, but as_dict=True. `dict_keys` having any
            value besides `None` implies as_dict=True.

        Returns
        -------
        Union[tuple, dict]
            Will return a tuple of (start datetime, end datetime) by default.
            These will be datetime objects if no `fmt` string is given.
            If as_dict=True, a dictionary is returned rather than a 
            tuple (using `dict_keys` as the keys if not None, and 
            ['start', 'end'] otherwise).

        """
        value = (self.start, self.end)
        if fmt is not None:
            value = (self.start.strftime(fmt), self.end.strftime(fmt))
        if as_dict or (dict_keys is not None):
            value = dict(zip(dict_keys or ['start', 'end'], value))
        return value 



    def ensure_unique(self) -> 'DatetimeRange':
        """ If start and end are the same, set end to start + 1 day """
        if self.start == self.end:
            return DatetimeRange(start=self.start, end=self.start + td(days=1))
        return self



    @property
    def distance(self):
        """ Absolute temporal distance between the start/end values """
        return abs(self.end - self.start)
    



