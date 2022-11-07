from .pretty_print import pretty_print
from ..exceptions import InvalidSelectionError

from typing import Iterable, Optional



def assert_contains(
    options : Iterable,                
    value   : Optional[str] = None,   
    label   : str           = 'value',
    e_type  = InvalidSelectionError, 
    **kwargs,                         
) -> None: 
    """Verify that the `options` iterable contains a given value.

    Checks that `options` contains either `value` (if given),
    or the keyword parameter(s) given via `kwargs`.

    Parameters
    ----------
    options  : Iterable
        Iterable that is checked for the given value(s).
    value    : str, optional
        Value that should be contained in `options`. If 
        this parameter is not given, a keyword parameter
        representing the value should be passed instead.
    label    : str, optional
        Label for the expected value, to be used in the
        message for the exception which is raised.
    e_type   : ExceptionType, optional
        Type of exception that will be raised if the 
        expected value is not found in `options`.
    **kwargs
        {`label`: `value`} pair(s) can be passed as 
        keyword arguments to the function as well. 

    Raises
    ------
    Exception
        By default InvalidSelectionError, though this 
        can be modified via the `e_type` parameter.

    Examples
    --------
    >>> colors = ['red', 'blue']
    >>> assert_contains(colors, color='green')
    InvalidSelectionError: Unknown color "green"
     Options are:
        red
        blue

    >>> letters = ['a', 'b', 'c']
    >>> assert_contains(**{
            'options' : letters,
            'value'   : 'd',
            'label'   : f'letter',
            'e_type'  : NotImplementedError,
        })
    NotImplementedError: Unknown letter "d"
     Options are:
        a
        b
        c

    """
    kwargs[label] = value  

    for label, value in kwargs.items():
        if (value is not None) and (value not in options):
            message = f'Unknown {label} "{value}"\n '
            message+= f'Options are:{pretty_print(list(options))}'
            raise e_type(message)
