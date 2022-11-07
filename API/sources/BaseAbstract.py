from functools import wraps
from abc import ABCMeta, ABC

STRICT_TYPECHECK = False


class BaseMeta(ABCMeta):
    """ Metaclass for class name string representation. """
    def __str__(self):  return self.__name__
    def __repr__(self): return self.__name__



class BaseAbstract(ABC, metaclass=BaseMeta):
    """ Base class for any other 'Base' classes. """
    def __str__(self):  return self.__class__.__name__
    def __repr__(self): return self.__class__.__name__

    def __getattribute__(self, attr):
        """ Provides type checking for class functions that use annotations """
        f = object.__getattribute__(self, attr)

        # If this is a function, check types for the given inputs
        if STRICT_TYPECHECK and callable(f):

            @wraps(f)
            def ensure_types(*args, **kwargs):
                f_name   = f.__func__.__code__.co_name
                f_params = f.__func__.__code__.co_varnames 
                f_types  = f.__func__.__annotations__
                keywords = dict(zip(f_params[1:], args))
                keywords.update(kwargs)

                for key, value in keywords.items():
                    if key in f_types and not isinstance(value, f_types[key]):
                        need  = f_types[key].__name__
                        found =  type(value).__name__
                        message = f'{self}.{f_name} parameter "{key}" must be'
                        message+= f' of type {need}, but found type {found}'
                        raise TypeError(message)
                        
                return f(*args, **kwargs)
            return ensure_types
        return f
    