from ..search  import search
from ..correct import correct 
from ..extract import extract
from ..plot    import plot
from ..write   import write
from ..search  import download

from celery import group


def extraction(global_config):
    """ Chain together the matchup extraction pipeline """
    k = {'global_config' : global_config}

    # Execute all steps in parallel over sensors
    return group([(      
              download.s(**k)              # 1. Download the specified tile
                                    
            | correct.s(ac_method=ac, **k) # 2. Correct L1 scene with each AC processor
            | extract.s(**k)               # 3. Extract window from L2 scene
            | plot.s(**k)                  # 4. Plot product from L2 scene
            | write.s(**k)                 # 5. Write the data
        ) for ac in global_config.ac_methods])

# ( group([
#     search.s(sensor, **k)    # 1. Search for matching scenes 

#     # Execute steps 2-5 in parallel over AC processors
#     | 
#     for sensor in global_config.sensors]) )

