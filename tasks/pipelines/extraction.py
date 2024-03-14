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
    
    if global_config.timeseries_or_matchups == 'matchups':
        
        return ( group([
                search.s(sensor, **k)    # 1. Search for matching scenes 
                | download.s(**k)              # 1. Download the specified tile

                # Execute steps 2-4 in parallel over AC processors
                | group([(                                          
                      correct.s(ac_method=ac, **k) # 2. Correct L1 scene with each AC processor
                    | extract.s(**k)     # 3. Extract window from L2 scene
                    | plot.s(**k)        # 4. Plot product from L2 scene
                    |   write.s(**k)     # 5. Write the data
                ) for ac in global_config.ac_methods])
            for sensor in global_config.sensors]) )
    if global_config.timeseries_or_matchups == 'timeseries':
        # Execute all steps in parallel over sensors
        if True:
            return (group([
                      download.s(**k).set(queue=global_config.queue)              # 1. Download the specified tile

                      | group([(

                        correct.s(ac_method=ac, **k).set(queue=global_config.queue ) # 2. Correct L1 scene with each AC processor
                        | extract.s(**k).set(queue=global_config.queue )               # 3. Extract window from L2 scene
                        | plot.s(**k).set(queue=global_config.queue )                  # 4. Plot product from L2 scene
                        | write.s(**k).set(queue=global_config.queue )                 # 5. Write the data
                    ) for ac in global_config.ac_methods])
                    ]) ) #for sensor in global_config.sensors
        else:
            return (group([
                      download.s(**k)              # 1. Download the specified tile
    
                      | group([(      
                                            
                        correct.s(ac_method=ac, **k) # 2. Correct L1 scene with each AC processor
                        | extract.s(**k)               # 3. Extract window from L2 scene
                        | plot.s(**k)                  # 4. Plot product from L2 scene
                        | write.s(**k)                 # 5. Write the data
                    ) for ac in global_config.ac_methods])
                    ]) ) #for sensor in global_config.sensors

# ( group([
#     search.s(sensor, **k)    # 1. Search for matching scenes 

#     # Execute steps 2-5 in parallel over AC processors
#     | 
#     for sensor in global_config.sensors]) )

