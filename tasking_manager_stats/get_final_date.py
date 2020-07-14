import argparse
import os
import pandas as pd
import sys
sys.path.append(os.path.join(os.getcwd()))

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Get the date of the latest validation of a project')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    project_id = args.project_id
    db = dm.Database(project_id, force_json_reading=True)
    final_date = db.compute_final_validation_date()
    print(f'Latest validation in the Tasking Manager {final_date}')
