from .assert_contains import assert_contains


def color(text: str, color_name: str = 'green') -> str:
    """Wrap the given text with unicode that changes the displayed color.

    Parameters
    ----------
    text       : str
        Text to color.
    color_name : str
        Name of the color that should be used.

    Returns
    -------
    str
        Returns `text` wrapped in unicode which changes the text color.

    """
    colors = {
        'gray'   : 90, 'grey' : 90,
        'red'    : 91,
        'green'  : 92,
        'yellow' : 93,
        'blue'   : 94,
        'magenta': 95,
        'cyan'   : 96,
        'white'  : 97,

        'bold'      : 1,
        'underline' : 4,  
    }
    assert_contains(colors, color_name, 'color')
    return f'\033[{colors[color_name]}m{text}\033[0m'

