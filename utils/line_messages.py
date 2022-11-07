import sys


def line_messages(messages: list, nbars: int = 1) -> None:
    """Allow multiline message updates via tqdm.

    Need to call print() after the tqdm loop, 
    equal to the number of messages which were
    printed via this function (to reset cursor).
    
    Parameters
    ----------
    messages : list
        List of strings to print, with the printed
        text updated on subsequent calls to the function.
    nbars    : int
        The number of tqdm bars the line messages 
        come after.

    Examples
    --------
        >>> nbars = 2
        >>> for i in trange(5):
        ...     for j in trange(5, leave=False):
        ...         messages = [i, i/2, i*2]
        ...         line_messages(messages, nbars)
        >>> for _ in range(len(messages) + nbars - 1): print()
        
    """
    for _ in range(nbars): print()
    for m in messages: print('\033[K' + str(m))
    sys.stdout.write('\x1b[A'.join([''] * (nbars + len(messages) + 1)))