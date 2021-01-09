import argparse
import os
import random
import sys
import time

from tasking_manager_stats.export_tasks_to_csv import export_tasks_to_csv

sys.path.append(os.path.join(os.getcwd()))

import tasking_manager_stats.data_management as dm
from tasking_manager_stats.project_stats import print_project_stats
from stats_ohsome import print_ohsome_stats


def get_args():
    parser = argparse.ArgumentParser(description='Print stats to update')
    parser.add_argument('input_file', type=str, help='File with project id line by line')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    with open(args.input_file, 'r') as f:
        projects = f.readlines()
    for line in projects:
        try:
            project_id = int(line.replace('\n', ''))
            print('=====================')
            print(f'PROJECT {project_id} :')
            db = dm.Database(project_id)
            if db.updated:
                export_tasks_to_csv(project_id)
                print_project_stats(project_id)
                print_ohsome_stats(project_id)
                time.sleep(30 + 30 * random.random())
            else:
                print('already up to date')
        except:
            pass
