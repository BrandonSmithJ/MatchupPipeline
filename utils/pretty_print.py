from typing import Iterable


def pretty_print(obj: Iterable, indent: str = '  ', _depth: int = 1) -> str:
    """Return a nicely formatted string of the given iterable object.

    Parameters
    ----------
    obj    : Iterable
        The iterable object to be printed.
    indent : str
        Indentation character(s) to use on each nested level.
    _depth : int
        Internal parameter used to indicate nesting depth.

    Returns
    -------
    str
        String which is a formatted representation of the given `obj`.
        
    """
    try:
        brackets = {
            dict  : '{',
            list  : '[',
            tuple : '(',
        }

        can_iter = lambda o: type(o) in [dict, list, tuple]
        safe_len = lambda o: getattr(o, '__len__', lambda: len(str(o)))()

        bracket = brackets.get(type(obj), '')
        maxlen  = max(map(safe_len, [[]] + list(obj or [])))
        newline = '\n' + ''.join([' '] * maxlen)
        linesep = '\n' + ''.join([indent] * _depth)
        items   = getattr(obj, 'items', lambda: obj or [])()

        # Parse contents by recursing if object is iterable
        pprint = lambda v: pretty_print(v, indent, _depth+1) 
        parse  = lambda v: pprint(v) if can_iter(v) else v 

        # Turn object contents into a formatted string
        to_str = lambda o: ( 
                 f'{str(o[0]):>{maxlen}} : {parse(o[1])}' if type(obj) is dict
            else f'{parse(o)}'                            
        ).replace('\n', newline)
       
        # Iterables with only a single item should be on one line 
        value = bracket + linesep + linesep.join(map(to_str, items))
        if safe_len(obj) <= 1 and not can_iter((list(items) + [None])[0]):
            value = value.replace(linesep, ' ').strip()
        return value

    except Exception as e: 
        print(f'pretty_print failed to parse object {obj}:\n{e}')
    except:
        print(f'pretty_print failed to parse object {obj}')
    return str(obj) 

