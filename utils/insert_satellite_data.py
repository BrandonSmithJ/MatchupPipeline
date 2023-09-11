# -*- coding: utf-8 -*-
import psycopg2
import psycopg2.extras



#scene_id = "S2A_MSIL1C_20201017T155251_N0209_R054_T18SUG_20201017T193914"


def psql_insert_scene_entry(scene_dict):
    geo_sql = f"SELECT geo_location_id FROM geo_location WHERE name = \'{scene_dict['site_name']}\'"
    
    sql = f"""INSERT INTO satellite_data(scene_id, data_quality, satellite, creation_date, overpass_date, data_path, geo_location_id) 
    VALUES(%s, %s, %s, CURRENT_TIMESTAMP, %s, %s, ({geo_sql})) ON CONFLICT (scene_id) DO UPDATE SET
    (scene_id, data_quality, satellite, creation_date, overpass_date, data_path, geo_location_id) = 
    (EXCLUDED.scene_id, EXCLUDED.data_quality, EXCLUDED.satellite, EXCLUDED.creation_date, EXCLUDED.overpass_date, EXCLUDED.data_path, EXCLUDED.geo_location_id);"""

    conn = None
    try:
        # read database configuration
        # connect to the PostgreSQL database
        conn = psycopg2.connect(service='stream-stage-rw')
        # create a new cursor
        cur = conn.cursor()
        # SQL values
        value_list = (scene_dict['scene_id'], scene_dict['data_quality'], scene_dict['satellite'], scene_dict['overpass_date'], scene_dict['data_path'])
        # execute the INSERT statement
        cur.execute(sql,value_list)
        # commit the changes to the database
        conn.commit()
        print('INSERT/UPDATE SUCCESSFUL!')
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def get_geo_from_tiles(tiles):
    
    proper_names = []
    for tile in tiles:
        
        sql = f"""SELECT geo_location.*,tiles_geo_location.* FROM geo_location INNER JOIN tiles_geo_location
        ON geo_location.geo_location_id=tiles_geo_location.geo_location_id
        WHERE (tiles_geo_location.tile_id LIKE \'%{tile}%\');"""
        
        conn = None
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(service='stream-stage-rw')
            # create a new cursor
            cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
            # execute the INSERT statement
            cur.execute(sql)
            results = cur.fetchall()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        
        assert results is not None, print(f"No sites were found for {tile}")
        
        if len(results) == 0:
            print(f"Unable to find {tile} in geo_location table, assigning default ID 57")
            name = 'Dummy'
            proper_names.append(name)
            continue
        
        for r in results:
            try:
                name = r['name']
                print(f"Site name {name} matched with {tile}")
                proper_names.append(name)
                break
            except:
                print(f"Unable to find {tile} in geo_location table, assigning default ID 57")
                name = 'Dummy'
                proper_names.append(name)
                break
    
    return proper_names



def insert_satellite_data(scene_id):
    if scene_id.startswith('LC'):
     #LC08_L1TP_001070_20200202_20200211_01_T2
        sat_num = int(scene_id.split('_')[0].replace('LC',''))
        satellite = f'Landsat{sat_num}'
        overpass_date = scene_id.split('_')[3]
        data_flag = scene_id.split('_')[-1].split('.')[0]
        tile = scene_id.split('_')[2]
    elif scene_id.startswith('S2A'):
    #S2A_MSIL1C_20230409T020651_N0509_R103_T52SFB_20230409T035534
        satellite = 'Sentinel2A'
        overpass_date = scene_id.split('_')[2]
        data_flag = 'L1C'
        tile = scene_id.split('_')[5]
    elif scene_id.startswith('S2B'):
    #S2B_MSIL1C_20230409T020651_N0509_R103_T52SFB_20230409T035534
        satellite = 'Sentinel2B'
        overpass_date = scene_id.split('_')[2]
        data_flag = 'L1C'
        tile = scene_id.split('_')[5]

    scene_dict = {}
    scene_dict['satellite']=satellite
    scene_dict['scene_id']=scene_id
    scene_dict['overpass_date']=overpass_date
    scene_dict['compressed_name']=f"{scene_id}.tar.gz"
    scene_dict['data_path']=f"/tis/stream/data/{scene_dict['compressed_name']}"
    scene_dict['data_quality']=data_flag
    scene_dict['site_name'] = get_geo_from_tiles([tile])[0]

    psql_insert_scene_entry(scene_dict)
