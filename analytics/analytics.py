from sqlalchemy.exc import OperationalError
from geopy.distance import distance
from os import environ
from time import sleep
import pandas as pd
import numpy as np
import json
import sqlalchemy


print('Waiting for the data generator...')
sleep(20)
print('ETL Starting...')

while True:
    try:
        psql_engine = sqlalchemy.create_engine(environ["POSTGRESQL_CS"], pool_pre_ping=True, pool_size=10)
        break
    except OperationalError:
        sleep(0.1)
print('Connection to PostgresSQL successful.')
# Write the solution here
# Calculate distance
def get_distance_udf(x):
    x=x.apply(json.loads).apply(pd.Series).reset_index(drop=True)
    
    x['latitude'] = x['latitude'].astype(float)
    x['longitude'] = x['longitude'].astype(float)
    
    x['next_latitude'] = x['latitude'].shift(1)
    x['next_longitude'] = x['longitude'].shift(1)
    
    total_distance = x.iloc[1:-1].apply(lambda row: distance((row['latitude'], row['longitude']),
                                                             (row['next_latitude'], row['next_longitude'])).km,
                                                             axis=1)
                             
    return total_distance.sum()

BATCH_SIZE = 1000
df = pd.read_sql_table('devices', psql_engine, chunksize=BATCH_SIZE)

dfs=[]
for d in df:
    d['time'] = pd.to_datetime(d['time'], unit='s')
    
    d = d.set_index('time').groupby([pd.Grouper(freq='1H'), 'device_id']).agg({
        'temperature': 'max',
        'location':lambda x: get_distance_udf(x)
        }).reset_index().rename(columns={'location':'distance'})
    d['time'] = d['time'].astype(np.int64)//10**9

    dfs.append(d)
df = pd.concat(dfs).reset_index(drop=True)

try:
    mysql_engine = sqlalchemy.create_engine(environ["MYSQL_CS"]) 
except OperationalError as e:
    print(e)
    sleep(0.1)

df.to_sql('devices_aggregated', mysql_engine, if_exists='append')

print('ETL completed successfully!')