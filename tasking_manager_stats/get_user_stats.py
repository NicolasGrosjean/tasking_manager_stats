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
    parser.add_argument('token', type=str, help='HOT tasking manager API token ')
    return parser.parse_args()


def get_user_stats(user_list, token):
    print('Download user data')
    users = pd.DataFrame()
    contributions_by_day = pd.DataFrame()
    for user in tqdm(user_list):
        url = 'https://tasking-manager-tm4-production-api.hotosm.org/api/v2/users/' + user + '/statistics/'
        r = requests.get(url, headers={'Accept': 'application/json', 'Accept-Language': 'en',
                                       'Authorization': 'Token ' + token})
        data = r.json()
        contrib_user = pd.DataFrame(data['contributionsByDay'])
        contrib_user['Contributor'] = user
        contributions_by_day = pd.concat([contributions_by_day, contrib_user], axis=0)
        del data['countriesContributed']
        del data['ContributionsByInterest']
        del data['contributionsByDay']
        df = pd.DataFrame(pd.Series(data)).transpose()
        df.index = [user]
        time.sleep(0.5 + random.random())

        url = 'https://tasking-manager-tm4-production-api.hotosm.org/api/v2/users/' + user + '/openstreetmap/'
        r = requests.get(url, headers={'Accept': 'application/json', 'Accept-Language': 'en',
                                       'Authorization': 'Token ' + token})
        data2 = r.json()
        for k in data2.keys():
            df[k] = data2[k]
        users = pd.concat([users, df], axis=0)
        time.sleep(0.5 + random.random())
    users['level'] = 'ADVANCED'
    users.loc[users['changesetCount'] < 500, 'level'] = 'INTERMEDIATE'
    users.loc[users['changesetCount'] < 250, 'level'] = 'BEGINNER'
    return users, contributions_by_day


if __name__ == '__main__':
    args = get_args()
    stats = pd.read_csv(args.stats, encoding='ISO-8859-1')
    user_stats, contributions_by_day = get_user_stats(stats['Author'].unique(), args.token)
    user_stats.to_csv(os.path.join(dm.get_data_dir(), 'user_stats.csv'))
    stats['date'] = stats['Year'].astype(str) + '-' + stats['Month'].astype(str) + '-' + stats['Day'].astype(str)
    stats = stats[['date', 'Author', 'Task', 'Project']].drop_duplicates()
    stats[(stats['date'] == '2020-3-28') & (stats['Author'] == 'Anaximandre')]
    contributions_by_day_cartong = stats.groupby(['date', 'Author']).count().Task.reset_index()
    contributions_by_day_cartong.columns = ['date', 'Contributor', 'CartONG_count']
    contributions_by_day_cartong['date'] = pd.to_datetime(contributions_by_day_cartong['date'])
    contributions_by_day['date'] = pd.to_datetime(contributions_by_day['date'])
    contributions_by_day = pd.merge(contributions_by_day, contributions_by_day_cartong, on=['Contributor', 'date'],
                                    how='left')
    contributions_by_day.to_csv(os.path.join(dm.get_data_dir(), 'contributions_day.csv'), index=None)
