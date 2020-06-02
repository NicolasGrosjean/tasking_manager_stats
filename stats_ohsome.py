import argparse
import datetime
import pandas as pd
import requests
from tqdm import tqdm

import os
import sys
sys.path.append(os.path.join(os.getcwd()))

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Compute stats with ohsome')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    return parser.parse_args()


def get_json_request_header():
    """
    Return the header for JSON request
    :return:
    """
    return {'Accept': 'application/json', 'Authorization': 'Token sessionTokenHere==', 'Accept-Language': 'en'}


def get_last_available_ohsome_date():
    url = 'http://api.ohsome.org/v0.9/elementsFullHistory/geometry?bboxes=0,0,0,0'\
          '&keys=landuse&properties=tags&showMetadata=false&time=2019-01-01,'
    test_time = datetime.datetime.now() - datetime.timedelta(days=30)
    status = 404
    while status == 404:
        r = requests.get(url + test_time.strftime('%Y-%m-%d'), headers=get_json_request_header())
        status = r.status_code
        test_time = test_time - datetime.timedelta(days=10)
    return test_time.strftime('%Y-%m-%d')


def download_ohsome_data(area, start_time, end_time, tag, tag_type=None):
    """
    Download data for the ohsome API
    :param area: Download area
    :param start_time: Start time of the full history OSM (format %Y-%m-%d)
    :param end_time: End time of the full history OSM (format %Y-%m-%d)
    :param tag: OSM tag on which data are filtered
    :param tag_type: OSM type 'node', 'way' or ‘relation’ OR geometry 'point', 'line' or 'polygon’; default: all 3 OSM types
    :return:
    """
    url = 'http://api.ohsome.org/v0.9/elementsFullHistory/geometry?' + area +\
          '&keys=' + tag + '&properties=tags&showMetadata=false&time=' + start_time + ',' + end_time
    if tag_type is not None:
        url += '&types=' + tag_type
    print(f'Extract {tag} data between {start_time} and {end_time}')
    r = requests.get(url, headers=get_json_request_header())
    return r.json()


def print_ohsome_stats(project_id):
    db = dm.Database(project_id)
    polygons = ''
    for polygon in db.get_perimeter_poly()['coordinates']:
        if polygons != '':
            polygons += '|'
        polygons += str(polygon).replace('[', '').replace(']', '').replace(' ', '')
    area = 'bpolys=' + polygons
    start_date = db.get_creation_date()
    end_date = db.compute_final_validation_date()
    if end_date == '1970-01-01':
        print('WARNING : No validation found !')
        end_date = db.get_latest_update_date()
    ohsome_max_date = get_last_available_ohsome_date()
    if datetime.datetime.strptime(ohsome_max_date, '%Y-%m-%d') < datetime.datetime.strptime(end_date, '%Y-%m-%d'):
        print(f'ohsome data end {ohsome_max_date} whereas the latest project update was {end_date}')
        exit(-1)
    data = download_ohsome_data(area, start_date, end_date, 'building', tag_type=None)
    print('Downloading building done.')

    print('Process building data')
    df = pd.DataFrame()
    for feature in tqdm(data['features']):
        df = pd.concat([df, pd.DataFrame(data=[(feature['properties']['@osmId'],
                                                feature['properties']['@validFrom'],
                                                feature['properties']['@validTo'])],
                                         columns=['osmId', 'validFrom', 'validTo'])], axis=0, ignore_index=True)
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

    print('Download highway stats')
    url = 'https://api.ohsome.org/v0.9/elements/length?' + area + \
          '&keys=highway&format=json&showMetadata=false&types=way&time=' + start_date + '%2F' + end_date + '%2FP1D'
    r = requests.get(url, headers=get_json_request_header())
    data = r.json()
    print('\nDelta highway (km):')
    print(round((data['result'][-1]['value'] - data['result'][0]['value']) / 1000))


if __name__ == '__main__':
    args = get_args()
    print_ohsome_stats(args.project_id)
