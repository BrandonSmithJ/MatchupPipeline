from ..exceptions import MissingFileError, BadArchiveError

from pathlib import Path
import shutil, zipfile, tarfile, bz2


def decompress(        
    archive     : Path, 
    destination : Path, 
    remove      : bool = True,
) -> None:
    """Decompress the given archive, raising exceptions as necessary.

    Parameters
    ----------
    archive     : Path
        Path to the archive file.
    destination : Path
        Path of the location to extract to.
    remove      : bool, optional
        If True, delete the archive after extraction.
    
    Raises
    ------
    MissingFileError
        The given archive does not exist.
    BadArchiveError 
        The extraction fails for any reason.
    
    """

    class BZ2Helper(bz2.BZ2File):
        """ Provides uniform interface for .bz2 extraction """
        def extractall(self, destination: str):
            with open(destination, 'wb') as f:
                shutil.copyfileobj(self, f)

    extension = ''.join(archive.suffixes)
    operators = {
        '.zip'    : lambda f: zipfile.ZipFile(f, 'r'),
        '.tar'    : lambda f: tarfile.open(f),
        '.tar.gz' : lambda f: tarfile.open(f, 'r:gz'),
        '.bz2'    : lambda f: BZ2Helper(f, 'rb'),
    }

    if not archive.exists():
        message = f'Archive does not exist at {archive}'
        raise MissingFileError(message)
    
    try:
        with operators[extension](archive) as f:
            f.extractall(destination.as_posix())

    except Exception as e:
        archive.replace(archive.with_name(f'badarchive_{archive.name}'))
        message = f'Unable to decompress archive {archive}: {e}'
        raise BadArchiveError(message)

    if remove: archive.unlink()
