class BadArchiveError(Exception):
    """ Raised when the downloaded archive file cannot be decompressed """
    pass


class MissingFileError(Exception):
    """ Raised when an expected file is missing """
    pass


class MissingProcessorError(Exception):
    """ Raised when an atmospheric correction processor install isn't found """
    pass 


class InvalidSelectionError(Exception):
    """ Raised when an invalid option is chosen for a selection """
    pass


class UnknownDatetimeError(Exception):
    """ Raised when a datetime cannot be determined """
    pass


class UnknownLatLonError(Exception):
    """ Raised when Lat/Lon cannot be determined """
    pass


class OutOfBoundsError(Exception):
    """ Raised when the requested location is out of bounds """
    pass


class AtmosphericCorrectionError(Exception):
    """ Raised when an AC processor fails """
    pass


class MultipleSensorsError(Exception):
    """ Raised when there are multiple sensor aliases found in a filename """
    pass


class FetchAPIError(Exception):
    """ Raised when all Sources fail for an API method """
    pass