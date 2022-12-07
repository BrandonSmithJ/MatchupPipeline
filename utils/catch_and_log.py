from functools import wraps
from pathlib import Path 
import traceback



def catch_and_log(filename: str) -> callable:
    """Decorator to catch and log exceptions.

    This decorator allows any code using a decorated function
    to continue running even if the underlying function raises
    an exception (assuming the code can handle the function 
    returning `None`).

    When an exception is raised, the exception and traceback
    are logged to pipeline/Logs/`filename`.

    """
    root = Path(__file__).parent.parent.joinpath('Logs')
    path = root.joinpath(filename)
    root.mkdir(exist_ok=True, parents=True)
    if path.exists(): path.write_text('')

    def decorator(function: callable):

        @wraps(function)
        def wrapper(*args, **kwargs):
            try: return function(*args, **kwargs)
            except Exception as e:
                with path.open('a+') as f:
                    f.write(f'{function.__name__}: {e}\n\n')
                    f.write(f'Args: {args}\n\n')
                    f.write(f'Kwargs: {kwargs}\n\n')
                    f.write(f'{traceback.format_exc()}\n\n\n\n')
        
        return wrapper
    return decorator

