import argparse
import os
import requests
import time
import random
from tqdm import tqdm
import pandas as pd

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Agregate users data from tasking manager API')
    parser.add_argument('merged_stats', type=str, help='Path of the merged stats CSV file')
    parser.add_argument('stats_one_author', type=str, help='Path of the merged stats 1 author by task type CSV file')
    return parser.parse_args()


def aggregate_merged_stats(merged_stats):
    df = merged_stats[['date', 'Author']].drop_duplicates()
    df = df.groupby('Author').count().date.reset_index()
    df.columns = ['Author', 'Nb_jours']
    df2 = merged_stats.groupby('Author').min().date.reset_index()
    df2.columns = ['Author', 'Start']
    df = pd.merge(df, df2, on='Author')
    df3 = merged_stats.groupby('Author').max().date.reset_index()
    df3.columns = ['Author', 'End']
    df = pd.merge(df, df3, on='Author')
    return df


def aggregate_merged_stats_one_author_by_task_type(merged_stats_one_author_by_task_type):
    df = merged_stats_one_author_by_task_type[merged_stats_one_author_by_task_type['Type'] == 'MAPPING']
    df = df.groupby('Author').count().Type.reset_index()
    df.columns = ['Author', 'Mapping_tasks']
    df2 = merged_stats_one_author_by_task_type[merged_stats_one_author_by_task_type['Type'] == 'VALIDATION']
    df2 = df2.groupby('Author').count().Type.reset_index()
    df2.columns = ['Author', 'Validation_tasks']
    df = pd.merge(df, df2, on='Author')
    return df


if __name__ == '__main__':
    args = get_args()
    merged_stats = pd.read_csv(args.merged_stats, encoding='ISO-8859-1')
    merged_stats['date'] = merged_stats['Year'].astype(str) + '-' + merged_stats['Month'].astype(str) + '-' + merged_stats['Day'].astype(str)
    merged_stats['date'] = pd.to_datetime(merged_stats['date'], yearfirst=True)
    user_stats = aggregate_merged_stats(merged_stats)
    merged_stats_one_author_by_task_type = pd.read_csv(args.stats_one_author, encoding='ISO-8859-1')
    user_stats2 = aggregate_merged_stats_one_author_by_task_type(merged_stats_one_author_by_task_type)
    user_stats = pd.merge(user_stats, user_stats2, on='Author')
    user_stats.to_csv(os.path.join(dm.get_data_dir(), 'agregated_user_stats.csv'), index=None)
