from .exceptions import ResultComparisonError, HaltOnFailureError
from .utils import color, get_dict_hash, pretty_print

from sentinelsat.exceptions import LTATriggered
from landsatxplore.errors import EarthExplorerError
from requests.exceptions import ReadTimeout

from typing import Callable, List, Optional
from functools import wraps
from pathlib import Path
import traceback, json, sys


OUTPUT_FOLDER = Path(__file__).parent.joinpath('Outputs')
OUTPUT_FOLDER.mkdir(exist_ok=True)


def get_results_path(**config):
    """ Get path to test config hash file """
    config = {k: str(v) for k, v in config.items()}
    return OUTPUT_FOLDER.joinpath(
        str(config.get('sensor', 'No Sensor')), 
        str(config.get('Source', 'No Source')),
        f'{get_dict_hash(config)}.json',
    )



def test_function(function : Callable) -> Callable:
    """ Decorator which tests whether a function raises an exception """

    class FormattedName:
        # Set the string representation of the function to be its name
        def __init__(self, f):               self.f = f
        def __call__(self, *args, **kwargs): return self.f(*args, **kwargs)
        def __str__(self):                   return self.f.__name__
        def __repr__(self):                  return self.f.__name__

    function = wraps(function)( FormattedName(function) )

    @FormattedName
    @wraps(function)
    def wrapper( 
        args,         # Testing args
        **f_kwargs,   # Keyword arguments to pass to function
    ) -> str:         # Returns pass/fail result string
        """ Determine whether the given function throws an exception """
        ignore_tb = (ReadTimeout, LTATriggered, EarthExplorerError)

        # Try to run the function, and catch any execution exceptions
        try: 
            message = run_function(args, function=function, **f_kwargs) or ''
            output  = color(f'PASS\n{message}'.strip(), 'green')

            if 'WARN:' in output: 
                message = message.replace('WARN: ', '')
                output  = color(f'WARN\n{message}'.strip(), 'yellow')

        # Only give warning if the config isn't implemented for the function
        except NotImplementedError as e: 
            output = color(f'DEBUG\nNot implemented: {e}', 'gray')

        # Don't show the traceback if the exception is a known error type
        except ignore_tb as e:
            output = color(f'FAIL\n{e.__class__.__name__}: {e}', 'red')

        # Label any other exception as failure, include traceback if requested
        except Exception as e:      
            output = color(f'FAIL\n{e.__class__.__name__}: {e}', 'red')
            if args.show_traceback:      
                output = f'{output}\n{traceback.format_exc()}\n'
        return output
    return wrapper



def run_function(args, **kwargs) -> Optional[str]:
    """
    Helper which executes a function and tests whether the 
    returned value matches with the expected value
    """
    result_path = get_results_path(**kwargs)
    result_path.parent.mkdir(exist_ok=True, parents=True)

    result   = dict(kwargs)
    function = kwargs.pop('function')
    result['output'], f_message = function(**kwargs)

    # If the expected outputs file doesn't yet exist, write the current output
    if not result_path.exists():
        with result_path.open('w+') as f:
            json.dump(result, f, indent=2, default=str)

    # Load the expected results
    with result_path.open() as f:
        expected_result = json.load(f)['output']

    # Ensure current results are in the same format as the expected results
    result = json.loads(json.dumps(result, default=str))['output']

    # Check that the result types are the same
    if type(expected_result) != type(result):
        message = f'For {function} ({result_path}), expected result type '
        message+= f'{type(expected_result)}, got {type(result)}'
        raise ResultComparisonError(message)

    # Ensure the results are iterable
    if not hasattr(expected_result, '__iter__'):
        expected_result = [expected_result]
        result = [result]

    # Check that the overall number of outputs is the same
    if len(expected_result) != len(result):
        message = f'Number of outputs changed in {result_path.name}'
        raise ResultComparisonError(message)


    # Check that all outputs are equal (to the first level, not a deep check)
    for idx, r_prev in enumerate(expected_result):
        if type(result) is dict:
            label  = f'Key "{r_prev}"'
            r_curr = result[r_prev]
            r_prev = expected_result[r_prev]
        else:
            label  = f'Index {idx}'
            r_curr = result[idx]

        if r_curr != r_prev:
            message = f'{label} has changed: {r_prev} -> {r_curr}'
            raise ResultComparisonError(message)
    return f_message



def run_tests(
    args, 
    iterables : List,       # List of test iterables to use 
    indent    : str = '  ', # Indentation character(s)
):
    """
    Run tests given a list of iterables containing the configuration
    parameters to use for the tests. The iterables parameter should 
    be a list of the form:
        iterables = [
            (config_key_1, [list of values to use for config_key_1]),
            (config_key_2, [list of values to use for config_key_2]),
            ...
            ('function',   [list/dict of test functions to apply]),
            ...
            ('kwargs',     [list/dict of kwargs to pass into each test function]),
            ...
            (config_key_n, [list of values to use for config_key_n]),
        ]

    Note that exactly one key in the iterables list must be 'function',
    which contains a list of different test functions that should be
    applied. As well, these functions should all be decorated with the
    @test_function decorator.

    Similarly, exactly one key in the iterables list _can_ be 'kwargs',
    which contains a list of different kwargs to pass to each test function -
    thus defining different test cases. 
    """

    def recursive_run(
        args, 
        iterables : List,       # List of test iterables to use 
        indent    : str = '  ', # Indentation character
        _indent   : str = '',   # Current indentation string
        **config,               # Parameters for the test function
    ):
        # If there are no iterables left, we're ready to run the test function
        if len(iterables) == 0:
            # First yield an empty string in order to print the label prior to 
            # executing a potentially long-running function
            yield ''

            # Then execute the function and yield results as appropriate
            config.update( config.pop('kwargs', {}) )
            function = config.pop('function')
            output   = function(args, **config).replace('\n', f'\n{_indent}')

            warn  = args.show_warnings or ('WARN'  not in output)
            debug = args.show_debugs   or ('DEBUG' not in output)
            if warn and debug:
                yield output
            if args.halt_on_fail and ('FAIL' in output):
                raise HaltOnFailureError(f'Halting due to failure in {function}')

        # Otherwise, continue recursing on the next configuration iterable
        else:
            config_key, iterable = iterables.pop(0)

            # Loop through all values of the current configuration key
            for key, value in enumerate( iterable ):

                # Ensure we use the dictionary key as the label 
                if type(iterable) is dict: key = value

                # Create the arguments for the next level of recursion
                config.update({
                    config_key : iterable[key], 
                    'args'     : args,
                    'iterables': list(iterables), 
                    'indent'   : indent,
                    '_indent'  : _indent + indent,
                })

                # Color the different label categories
                if config_key == 'function': value = color(value, 'blue')
                if config_key == 'Source':   value = color(value, 'cyan')
                if config_key == 'sensor':   value = color(value, 'magenta')
                if config_key == 'kwargs':   value = color(value, 'white')

                # Iterate over outputs, modifying and passing them up the stack
                for i, output in enumerate( recursive_run(**config) ): 

                    # We're at the bottom of the stack, output is from function
                    if len(iterables) == 0: 
                        output = f'{_indent}{value} : {output}'

                    # We're above the bottom, and we label the first output
                    elif i == 0:
                        output = f'{_indent}{value} \n{output}'

                        # We're at the top of the stack
                        if _indent == '':
                            output = f'\n{output}'
                    yield output


    # Initial call, top of recursive stack; prints outputs passed up the stack
    try: 
        generator = recursive_run(args, list(iterables), indent)
        for output in generator:
            print(output, end='') # Print the label
            sys.stdout.flush()
            output = next(generator)
            print(output)         # Print the result
    except HaltOnFailureError as e:
        print(color(f'{e.__class__.__name__}: {e}', 'red'))
        print(f'Testing configuration: {args}\n{pretty_print(dict(iterables))}')
        sys.exit(1)
