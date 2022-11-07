import numpy as np 


def bitmask_parse(bitmask: np.ndarray, debug: bool = False) -> np.ndarray:
    """Parse a bitmask into the flag indices it represents.

    Parameters
    ----------
    bitmask : np.ndarray
        Bitmask array to parse.
    debug   : bool, optional
        If True, perform slower equality checks.

    Returns
    -------
    np.ndarray
        Returns a boolean array with bits unpacked
        along the last dimension.

    """
    debug = True
    if debug:
        # Take a random subset rather than the entirety, to save time / memory
        random_idx = np.random.choice(np.arange(bitmask.size), 10000)
        orig = bitmask.flatten()[random_idx]

    shape   = bitmask.shape
    bitmask = bitmask.flatten()[:, None].byteswap()
    bitmask = np.unpackbits(bitmask.view(np.uint8), axis=1)[:, ::-1]
    bitmask = bitmask.astype(bool)

    if debug:
        recalc  = np.zeros(orig.shape)
        row,col = np.where(bitmask[random_idx])
        np.add.at(recalc, row, 2 ** col)
        if not (recalc == orig).all():
            idxs = np.where(recalc != orig)[0]
            print('Original:',orig[idxs[0]])
            print('Recalced:',recalc[idxs[0]])
            print('Bitmask: ',bitmask[idxs[0]])
            raise Exception('Bitmask flags calculated incorrectly')
    return bitmask.reshape(shape+(-1,))



def print_bitmask_stats(bitmask: dict) -> None:
    """ Neatly print stats for the given bitmask dictionary """
    print('\nBitmask stats:')
    for i, (key, mask) in enumerate(bitmask.items()):
        print(f'\t{key:>12} | {mask.sum():,} / {mask.size:,}')