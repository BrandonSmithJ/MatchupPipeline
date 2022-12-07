class ResultComparisonError(Exception): 
    """ Raised when function results don't match expected results """
    pass


class HaltOnFailureError(Exception):
    """ Raised when test run halts due to exception within test function """
    pass

