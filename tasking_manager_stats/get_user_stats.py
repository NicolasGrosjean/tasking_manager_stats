import argparse
import os
import requests
import time
import random
from tqdm import tqdm
import pandas as pd

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Get users data from tasking manager API')
    parser.add_argument('stats', type=str, help='Path of the stats CSV file containing contributors')
    return parser.parse_args()


def get_user_stats(user_list):
    print('Download user data')
    users = pd.DataFrame()
    for user in tqdm(user_list):
        url = 'https://tasks.hotosm.org/api/v1/stats/user/' + user
        r = requests.get(url, headers={'Accept': 'application/json', 'Accept-Language': 'en'})
        data = r.json()
        df = pd.DataFrame(pd.Series(data)).transpose()
        df.index = [user]
        time.sleep(0.5 + random.random())

        url = 'https://tasks.hotosm.org/api/v1/user/' + user + '/osm-details'
        r = requests.get(url, headers={'Accept': 'application/json', 'Accept-Language': 'en'})
        data2 = r.json()
        for k in data2.keys():
            df[k] = data2[k]
        users = pd.concat([users, df], axis=0)
        time.sleep(0.5 + random.random())
    users['level'] = 'ADVANCED'
    users.loc[users['changesetCount'] < 500, 'level'] = 'INTERMEDIATE'
    users.loc[users['changesetCount'] < 250, 'level'] = 'BEGINNER'
    return users


if __name__ == '__main__':
    args = get_args()
    stats = pd.read_csv(args.stats, encoding='ISO-8859-1')
    user_stats = get_user_stats(stats['Author'].unique())
    user_stats.to_csv(os.path.join(dm.get_data_dir(), 'stats', 'user_stats.csv'))
