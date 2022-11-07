from typing import Any
import inspect



def variable_name(var: Any) -> str:
    """Return the name of the passed variable.

    Parameters
    ----------
    var : Any
        Variable to determine the name of.

    Returns
    -------
    str
        String representation of the variable's name in the code.

    References
    ----------
    .. [1] https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
    
    """
    for fi in reversed(inspect.stack()):
        names = [name for name, val in fi.frame.f_locals.items() if val is var]
        if len(names) > 0: return names[0]