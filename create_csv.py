import pandas as pd 
import numpy as np
import re
import os
os.chdir(os.getcwd())

from pipeline.__main__ import load_insitu_data
from pipeline.utils import pretty_print, bitmask_l2gen
from pipeline.parameters import get_args 
from pathlib import Path


def safe_number(v, methods=[int, float, str]):
    """ Safely parse a number when possible """
    if v.strip() == '--': return np.nan
    for method in methods:
        try: return method(str(v).strip())
        except: pass



def fix_coords(line):
    """ For loc.csv: replace values of the form (a, b) with a,b """
    return re.sub(r'\((-?\d), (-?\d)\)', r'\1<>\2', line)



def deserialize(line, separators=['||', '<>', ',']):
    """ Invert the serialization procedure """
    if len(separators) and separators[0] in line:
        recurse = lambda v: deserialize(v, separators[1:])
        return list(map(recurse, line.split(separators[0])))
    return safe_number(line.strip())



def parse_feature(global_config, idxs, features, name):
    """ Parse the requested feature into a DataFrame """
    columns = [features[name], idxs]
    i_names = ['row', 'col', name]
    banded  = f'{name}_bands' in features 
    print(name)
    #breakpoint()
    # Handle special files
    if name == 'meta':
        feature = pd.DataFrame(features[name][1:], columns=features[name][0])
        feature.columns = pd.MultiIndex.from_product([[name], feature.columns])
        return feature

    # Parse feature with bands (brdf for some reason does not have _bands)
    elif banded or name == 'brdf':
        columns+= [features[f'{name.replace("brdf", "Rrs")}_bands']]
        i_names+= ['wvl']

        feature = pd.DataFrame({i: 
            {(x, y, name, band) : value
                for (x, y), values in zip(coords, samples)
                for band, value in zip(bands, values)
            } for i, (samples, coords, bands) in enumerate(zip(*columns))   
        })

    # Parse any other single-valued features
    else:
        feature = pd.DataFrame({i: 
            {(x, y, name) : value
                for (x, y), value in zip(coords, samples)
            } for i, (samples, coords) in enumerate(zip(*columns))   
        })

    # Remove unrealistic feature values
    if name in ['Rrs', 'rhos', 'rhot']:
        feature[feature >= 10] = np.nan
        feature[feature <= -1] = np.nan

    # Gather requested pixels, and check number valid per sample
    feature.index.names = i_names
    window  = global_config.extract_window
    #print('window size')
    #print(window)
    w_range = list(range(-window, window+1))
    feature = feature[feature.index.get_level_values('row').isin(w_range)]
    feature = feature[feature.index.get_level_values('col').isin(w_range)]
    n_valid = (~feature.isna()).groupby(level=['row', 'col']).any().sum()

    # Set sample flag to be the bits for all pixel flags set within the window
    #print('before')
    #print(feature.shape)
    #print(feature.columns)
    #print(i_names[2:])
    if name in ['l2_flags', 'bitmask']:
        or_flag = lambda f: np.bitwise_or.reduce(f.dropna().to_numpy().astype(int))
        feature = feature.groupby(level=i_names[2:]).agg(or_flag).T

    # Take the median over the window
    else: #feature = feature.groupby(level=i_names[2:]).median().T
        #feature = feature.groupby(level=i_names[2:]).iloc[:,[0,1,2,3,4,5,9,10,14,15,19,20,21,22,23,24]].median().T
        #print('median: ') 
        feature = feature.groupby(level=i_names[2:]).median().T 
    # print('after')
    # print(feature.shape)
    # print(feature.columns)

    # Ensure all features have two levels
    if feature.columns.nlevels == 1:
        feature.columns.name = None
        feature.columns = pd.MultiIndex.from_product([[name], feature.columns])

    # Store the number of valid window pixels
    if '_bands' not in name:
        feature[f'{name}_valid_pct'] = n_valid / len(w_range) ** 2
    return feature 



def create_valid_mask(global_config, data, ac_method):
    """ Create a mask column which looks at valid pixels and l2 flags """
    #assert(ac_method in ['l2gen', 'acolite', 'polymer','aquaverse']), ac_method
    full_mask = np.zeros(len(data)).astype(bool)

    key = 'Rrs_valid_pct'
    if key in data:
        mask = data[key] < 0.5
        print(f'{mask[~full_mask].sum()} samples newly masked by window count')
        full_mask |= mask

    if 'l2_flags' in data and ac_method == 'l2gen':
        flag = data['l2_flags'].to_numpy().astype(int)
        mask = bitmask_l2gen(flag, ac_method, verbose=True)
        print(f'{mask[~full_mask].sum()} samples newly masked by l2 flags')
        full_mask |= mask.squeeze()

    print(f'Found {(~full_mask).sum()} / {len(data)} valid samples ({full_mask.sum()} filtered) ')
    data['valid'] = ~full_mask
    return data



def create_csv(global_config, insitu, path):
    """ Create the csv file for the given matchup folder """
    # Read and deserialize all files
    data = {}
    for filename in path.glob('*.csv'):

        # Skip loc file - same info is contained within window_* files
        if filename.stem == 'loc': continue
        
        #if filename.stem == 'loc': continue

        with filename.open() as f:
            lines = map(fix_coords, f.readlines())
            lines = map(deserialize, lines)
        data[filename.stem] = list(lines)
    
    #data_dict = pd.DataFrame.from_dict(data)
    #data_dict.to_csv(path.with_name(f'{path.name}.csv'), na_rep='nan', index=None)
    
    # Parse into DataFrames and concatenate
    idxs  = data.pop('window_idxs')
    parse = lambda name: parse_feature(global_config, idxs, data, name)
    data  = pd.concat(map(parse, data), axis=1)
    data  = create_valid_mask(global_config, data, path.name)
    #data  = data.drop_duplicates(('meta','uid'))
    data.to_csv(path.with_name(f'{path.name}_01.csv'), index=None)
    
    data  = data.set_index(('meta', 'uid'))
    data.index.name = 'uid'
    #print(data.index)
    #print(data.loc[:,'uid'])
    #breakpoint()
    
    #insitu['uid'] = data.index
    print(insitu.head())
    insitu.to_csv(path.with_name(f'{path.name}_1.csv'), index=None)     
    data.to_csv(path.with_name(f'{path.name}_2.csv'), index=None)
    
    #insitu.iloc[0,:] = insitu.columns
    
    data  = insitu.join(data, how='right', lsuffix='insitu_').reset_index()
    #data  = insitu.join(data.set_index('uid'), on='uid',how='right').reset_index()
    print(data.head())
    data.to_csv(path.with_name(f'{path.name}_3.csv'), index=None)
    
    columns = []
    for i in range(0, data.shape[1]):
        if str(data.columns[i][0]) in ['Rrs','rayleigh_corrected','VZA','VAA','sena','senz']:#, 'rhos', 'rhot']:    
            col = str(data.columns[i][0]) + '(' + str(data.columns[i][1]) + ')'
        else:
            if data.columns[i][0] in ["meta"]:
                col = data.columns[i][1]
            else:
                col = data.columns[i][0]
        columns.append(col)
    
    data.columns = columns
    data = data.dropna()
    #data = data.drop_duplicates('ins_chl')
    data.to_csv(path.with_name(f'{path.name}.csv'), na_rep='nan', index=None)
    #data.to_csv(path.with_name(f'{path.name}.csv'), index=None)     

def main():
    global_config = gc = get_args(validate=False)
    print(f'\nCollecting matchups using parameters: {pretty_print(gc.__dict__)}\n')
    
    ins_path = Path(global_config.insitu_path)
    #print(global_config.datasets)
    #breakpoint()
    #path = ins_path.joinpath(global_config.datasets[0], 'parsed.csv')
    #insitu = pd.read_csv(path)
    
    #print(insitu.head())
    insitu = load_insitu_data(gc)
    insitu.columns = pd.MultiIndex.from_product([insitu.columns, ['']])
    insitu = insitu.set_index('uid')

    for dataset in global_config.datasets:
        for sensor in global_config.sensors:
            for ac in global_config.ac_methods:
                path = global_config.output_path.joinpath(dataset, sensor, ac,'Matchups')

                if path.exists():
                    create_csv(global_config, insitu, path)


if __name__ == '__main__':
    main()
