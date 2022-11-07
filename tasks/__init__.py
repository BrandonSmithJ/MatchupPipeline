# Context manager
from .managers import CeleryManagerMulti as CeleryManager

# Individual tasks
from .shutdown import shutdown
from .search   import search
from .correct  import correct 
from .extract  import extract
from .write    import write

# Pipelines (task combinations)
from .pipelines import extraction_pipeline as create_extraction_pipeline
