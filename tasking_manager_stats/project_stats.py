import argparse
import os
import pandas as pd

import sys
sys.path.append(os.path.join(os.getcwd()))

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Print some stats about the project')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    return parser.parse_args()


def print_project_stats(project_id):
    stats_dir = os.path.join(dm.get_data_dir(), 'stats')
    os.makedirs(stats_dir, exist_ok=True)
    csv_file = os.path.join(stats_dir, str(project_id) + '.csv')
    df = pd.read_csv(csv_file, encoding='ISO-8859-1')
    contributor_nb = len(df['Author'].unique())
    df2 = df[['Type', 'Duration', 'Author', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']].drop_duplicates()
    mapping_time = df2.loc[df2['Type'] == 'MAPPING', 'Duration'].sum()
    validation_time = df2.loc[df2['Type'] == 'VALIDATION', 'Duration'].sum()
    print(f'Mapping time : {mapping_time/3600:.1f}h')
    print(f'Validation time : {validation_time/3600:.1f}h')
    print(f'Contributor number : {contributor_nb}')


if __name__ == '__main__':
    args = get_args()
    print_project_stats(args.project_id)
