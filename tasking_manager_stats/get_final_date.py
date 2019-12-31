import argparse
import os
import pandas as pd
import sys
sys.path.append(os.path.join(os.getcwd()))

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Generate a CSV file with task data')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    project_id = args.project_id
    db = dm.Database(project_id, force_json_reading=True)
    final_date = pd.to_datetime('1970-01-01').date()
    for task_id in db.get_task_ids():
        if str(task_id) not in db.get_task_history():
            print(f'Task {task_id} missing')
            continue
        task_data = db.get_task_history()[str(task_id)]
        for task_hist in task_data['taskHistory']:
            if task_hist['actionText'] == 'VALIDATED' and task_hist['action'] == 'STATE_CHANGE':
                date = pd.to_datetime(task_hist['actionDate']).date()
                if date > final_date:
                    final_date = date
    print(f'Latest validation in the Tasking Manager {final_date}')
