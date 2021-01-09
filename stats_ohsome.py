import argparse
import datetime
import json
import pandas as pd
import requests
from tqdm import tqdm
import logging

import os
import sys
sys.path.append(os.path.join(os.getcwd()))

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Compute stats with ohsome')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    parser.add_argument('-project_list', type=str,
                        help='File containing a list of project id to compute building stats on all of them')
    return parser.parse_args()


class NoDataException(Exception):
    pass


class URLTooLongException(Exception):
    pass


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
    logging.info(f'Extract {tag} data between {start_time} and {end_time}')
    r = requests.get(url, headers=get_json_request_header())
    if r.status_code == 414:
        raise URLTooLongException()
    elif r.status_code != 200:
        logging.error(json.loads(r._content.decode())['message'])
        r.raise_for_status()
    return r.json()


def download_project_ohsome_data(area, start_date, end_date):
    ohsome_max_date = get_last_available_ohsome_date()
    if datetime.datetime.strptime(ohsome_max_date, '%Y-%m-%d') < datetime.datetime.strptime(end_date, '%Y-%m-%d'):
        logging.info(f'ohsome data end {ohsome_max_date} whereas the latest project update was {end_date}')
        return
    return download_ohsome_data(area, start_date, end_date, 'building', tag_type=None)


def get_project_param(project_id):
    db = dm.Database(project_id)
    area = 'bboxes=' + str(db.get_perimeter_bounding_box()).replace('[', '').replace(']', '').replace(' ', '')
    start_date = db.get_creation_date()
    end_date = db.compute_final_validation_date()
    if end_date == '1970-01-01':
        logging.warning('No validation found !')
        end_date = db.get_latest_update_date()
    return area, start_date, end_date


def ohsome_to_df(data):
    df = pd.DataFrame()
    if len(data['features']) == 0:
        raise NoDataException()
    for feature in tqdm(data['features']):
        df = pd.concat([df, pd.DataFrame(data=[(feature['properties']['@osmId'],
                                                feature['properties']['@validFrom'],
                                                feature['properties']['@validTo'])],
                                         columns=['osmId', 'validFrom', 'validTo'])], axis=0, ignore_index=True)
    df['validFrom'] = pd.to_datetime(df['validFrom'])
    df['validTo'] = pd.to_datetime(df['validTo'])
    return df


def print_ohsome_stats(project_id):
    area, start_date, end_date = get_project_param(project_id)
    data = download_project_ohsome_data(area, start_date, end_date)
    print('Downloading building done.')

    print('Process building data')
    df = ohsome_to_df(data)

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


def get_building_data(project_id):
    building_file = os.path.join(dm.get_data_dir(), 'buildings', f'{project_id}.csv')
    if os.path.exists(building_file):
        # Data already computed
        return pd.read_csv(building_file)

    ohsome_file = os.path.join(dm.get_data_dir(), 'ohsome', f'{project_id}_buildings.json')
    if os.path.exists(ohsome_file):
        # Read local ohsome data
        with open(ohsome_file, 'r') as f:
            data = json.load(f)
    else:
        # Download data from ohsome
        data = download_project_ohsome_data(*get_project_param(project_id))
        with open(ohsome_file, 'w') as f:
            json.dump(data, f)

    # Format ohsome data in dataframe
    df = ohsome_to_df(data)

    # Count the building number by date at 00:00:00
    count_df = pd.DataFrame()
    for date in pd.date_range(pd.Timestamp(df['validFrom'].min().date()), df['validTo'].max()):
        building_nb = ((df['validFrom'] <= date) & (df['validTo'] >= date)).sum()
        count_df = pd.concat([count_df, pd.DataFrame(data=[(date, building_nb)], columns=['Date', 'BuildingNb'])],
                             axis=0, ignore_index=True)
    count_df.to_csv(building_file, index=None)
    return count_df


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    args = get_args()
    if args.project_list is None:
        print_ohsome_stats(args.project_id)
    else:
        with open(args.project_list, 'r') as f:
            projects = f.readlines()
        for line in projects:
            project_id = int(line.replace('\n', ''))
            print('=====================')
            print(f'PROJECT {project_id} :')
            try:
                get_building_data(project_id)
            except NoDataException as e:
                print(f'No buildings found for {project_id}')
            except URLTooLongException:
                print(f'Perimeter too complex for {project_id}')
