from functools import partial
import numpy as np 


def unstack(
    data         : list, 
    keep_last    : bool = False, 
    remove_empty : bool = True,
) -> (list, callable):
    """Returns a flattened list from a nested list of unlimited depth.

    This function flattens a nested list of arbitrary depth, and also 
    returns a function which re-stacks a list (with the same length as the
    previously returned flattened list) into the original nesting format.

    Parameters
    ----------
    data      : list
        The list that should be flattened
    keep_last : bool, optional
        If True, will keep the last nested list intact in the 
        returned flat list e.g. [[1,2],[3,4]] instead of [1,2,3,4].
    remove_empty : bool, optional
        If True, will discard empty bottom lists when unstacking
        with keep_last=True, but still replace them when restacking.

    Returns
    -------
    list
        Flattened representation of the list given as input.
    callable
        Function that will re-stack a flat list in the same format
        as the original list that was given as input (so long as 
        it is the same length as the returned flat list).

    Examples
    --------
    >>> nested = [[1, 2], 3, [4, [5, 6, [7]]], [8]]
    >>> flattened, restack = unstack(nested)
    >>> flattened
    [1, 2, 3, 4, 5, 6, 7, 8]
    >>> restack([0] * len(flattened))
    [[0, 0], 0, [0, [0, 0, [0]]], [0]]

    >>> nested = [[[1, 2], [3, 4], []], [[5, 6], [], [7], [8]]]
    >>> unstack(nested)[0]
    [1, 2, 3, 4, 5, 6, 7, 8]
    >>> unstack(nested, keep_last=True, remove_empty=False)[0]
    [[1, 2], [3, 4], [], [5, 6], [], [7], [8]]    

    """ 
    if isinstance(data, list):
        if not remove_empty or len(data) > 0:
            if not keep_last or (len(data) and isinstance(data[0], list)):
                counts   = []
                restacks = []
                new_data = []

                for i in data:
                    flat, restack = unstack(i, keep_last, remove_empty)
                    counts.append(len(flat))
                    restacks.append(restack)
                    new_data += flat

                def restack(d, counts, restacks):
                    i_counts = np.cumsum([0] + counts)
                    message  = f'To restack, the given list ({len(d)}) '
                    message += f'must be the same size as the flattened '
                    message += f'list ({i_counts[-1]})'
                    assert(len(d) == i_counts[-1]), message
                    return [f(d[start:end]) for f, start, end in 
                            zip(restacks, i_counts[:-1], i_counts[1:])]

                return new_data, partial(restack, counts=counts, restacks=restacks)
        else:   return [], lambda x: []
    return [data], lambda x: x[0] 
