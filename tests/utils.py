from ..utils import assert_contains, pretty_print, color
import hashlib


def get_dict_hash(
	d         : dict,           # Dictionary that should be hashed 
	hash_name : str = 'sha256', # Name of the algorithm to use
):
	''' 
	Get a pseudo-unique identifier for a set of key:values contained in a dict 
	'''
	assert_contains(hashlib.algorithms_available, hash_name, 'hashing function')
	keyval_string = ','.join([f'{k}:{d[k]}' for k in sorted(d.keys())])
	return getattr(hashlib, hash_name)(keyval_string.encode('utf-8')).hexdigest()
