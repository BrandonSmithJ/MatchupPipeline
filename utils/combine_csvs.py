import numpy as np
from pathlib import Path
import os,csv
import pandas as pd

out_path = Path("/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/MODIS_VIIRS_test_image/MOD/l2gen/Matchups/scenes/")

out_path = Path("/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/OLI_test_image_Wachusett_reservoir_timeseries/MSI/aquaverse/Matchups/scenes/")

def combine_csvs(out_path):
    directories = os.listdir(out_path)
    directories = [f for f in directories if not os.path.isfile(f)]
    data_dictionary = {}



    for k,directory in enumerate(directories):
        print(k,"of",len(directories), " | ",directory.split('/')[-1])
        out_dir = out_path.joinpath(directory)
        files = os.listdir(out_dir)
        #print(files)
        data_dictionary[directory] = {}
        for f in files:
            out_f = out_dir.joinpath(f)
            #print(out_f)
            #if 'meta' in f:
            #    print(f)
            try:
                data_dictionary[directory][f] = pd.read_csv(out_f,header=None,sep='{').values
            except:
                print("Failed to load:", directory,f)
    for i,scene_id in enumerate(data_dictionary.keys()):
        variable_length_holder = {}
        variable_separators    = {}

        for variable in data_dictionary[scene_id].keys():
            variable_length_holder[variable] = len(data_dictionary[scene_id][variable])
            variable_separators[variable]    = sum( [ str(i[0]).count('||') for i in data_dictionary[scene_id][variable]])
            if variable == 'meta.csv':
                variable_length_holder[variable] = variable_length_holder[variable] - 1
        [variable_separators[var_key] for var_key in variable_separators.keys()]
        separators_list = [variable_separators[var_key] for var_key in variable_separators.keys()]
        data_dictionary[scene_id]['data_lens'] = variable_length_holder
        data_dictionary[scene_id]['valid']     = (len(set([data_dictionary[scene_id]['data_lens'][var_key] for var_key in data_dictionary[scene_id]['data_lens'].keys()])) == 1) and (0 not in separators_list)
        print(scene_id,len(data_dictionary[scene_id].keys()),data_dictionary[scene_id]['data_lens']) 
        if data_dictionary[scene_id]['valid']: 
            
            for variable in data_dictionary[scene_id].keys():
                if not 'csv' in variable: continue
                out_var = out_path.parent.joinpath(variable)

                if (not i == 0):
                    if (variable in os.listdir(out_path.parent)) and (len([key for key in os.listdir(out_path.parent) if 'csv' in key])==len([key for key in data_dictionary[scene_id].keys() if 'csv' in key])):
                        print("Writing", i, variable)
                    else:
                        print("Not writing",variable,i)
                        continue

                if i == 0:
                    if '.csv' in str(out_var) and os.path.exists(out_var): os.remove(out_var)
            
                with open(out_var,'a',newline='\n') as csv_var: 
                    for j,row in enumerate(data_dictionary[scene_id][variable]):
                        for var_str in row: 
                            if variable == 'meta.csv' and (j ==0 and i !=0): 
                                continue
                            csv_var.write(var_str+'\n')

    print("Original data length:", len(directories))
    print([f for f in os.listdir(out_path.parent) if os.path.isfile(f)])

    final_var_lengths = []
    for final_var in [f for f in os.listdir(out_path.parent) if os.path.isfile( out_path.parent.joinpath(f))]:
        final_var_path = out_path.parent.joinpath(final_var)
        final_var_csv  = pd.read_csv(final_var_path,header=None,sep='{').values
        if final_var == 'meta.csv':
            meta_offset = 1
        else:
            meta_offset = 0
    
        final_var_lengths.append(len(final_var_csv)-meta_offset)
        print("Final variable:", final_var,"Length:",len(final_var_csv))
    print(f"{len(final_var_lengths)} variables have length of:", set(final_var_lengths))

    if len(set(final_var_lengths)) == 1:
        print("Successfully processed, variables have same lengths")
    else:
        print("Failed to process, variables have different lengths")
        assert(0)

    #print(data_dictionary)
