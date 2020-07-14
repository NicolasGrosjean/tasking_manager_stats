import argparse
import os
import pandas as pd

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Filter merged stats between two dates')
    parser.add_argument('min_date', type=str, help='Included min date in filtering in DD-MM-YYYY')
    parser.add_argument('max_date', type=str, help='Included max date in filtering in DD-MM-YYYY')
    return parser.parse_args()


def filter_data(filename, min_date, max_date):
    merge_stats = pd.read_csv(os.path.join(dm.get_data_dir(), filename), encoding='ISO-8859-1')
    merge_stats['Date'] = pd.to_datetime(merge_stats[['Year', 'Month', 'Day']])
    merge_stats = merge_stats[merge_stats['Date'] >= pd.to_datetime(min_date, dayfirst=True)]
    merge_stats = merge_stats[merge_stats['Date'] <= pd.to_datetime(max_date, dayfirst=True)]
    del merge_stats['Date']
    merge_stats.to_csv(os.path.join(dm.get_data_dir(), min_date + '_' + max_date + '_' + filename), index=None)


if __name__ == '__main__':
    args = get_args()
    filter_data('merged_stats.csv', args.min_date, args.max_date)
    filter_data('merged_stats_one_author_by_task_type.csv', args.min_date, args.max_date)
