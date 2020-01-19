import json
import pandas as pd
from tqdm import tqdm


start_date = '2019-02-18'
end_date = '2019-11-30'
project_id = '5758'

with open('D:\Documents\AAA_' + project_id + '_building_p_osm_'+ start_date + '_' + end_date + '.geojson') as f:
    data = json.load(f)

df = pd.DataFrame()
for feature in tqdm(data['features']):
    df = pd.concat([df, pd.DataFrame(data=[(feature['properties']['@osmId'],
                                            feature['properties']['@validFrom'],
                                            feature['properties']['@validTo'])],
                                     columns=['osmId', 'validFrom', 'validTo'])],axis=0, ignore_index=True)
df['validFrom'] = pd.to_datetime(df['validFrom'])
df['validTo'] = pd.to_datetime(df['validTo'])

print('Kept without modification :')
kept = ((df['validFrom'] == start_date + ' 00:00:00') & (df['validTo'] == end_date + ' 00:00:00')).sum()
print(kept)

df2 = df.groupby('osmId').agg({'validFrom': min, 'validTo': max})

print('\nDeleted :')
print(((df2['validFrom'] == start_date + ' 00:00:00') & (df2['validTo'] < end_date + ' 00:00:00')).sum())

print('\nUpdated :')
print(((df2['validFrom'] == start_date + ' 00:00:00') & (df2['validTo'] == end_date + ' 00:00:00')).sum() - kept)

print('\nCreated :')
print(((df2['validFrom'] > start_date + ' 00:00:00') & (df2['validTo'] == end_date + ' 00:00:00')).sum())

print('\nTotal current :')
print((df2['validTo'] == end_date + ' 00:00:00').sum())
