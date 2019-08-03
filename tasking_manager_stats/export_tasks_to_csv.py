import argparse
import os
import pandas as pd

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Generate a CSV file with task data')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    return parser.parse_args()


def compute_task_data(database):
    start = database.get_start_date()
    project = database.get_project_id()
    raw_data = pd.DataFrame()
    for task_id in database.get_task_ids():
        if str(task_id) not in database.get_task_history():
            print(f'Task {task_id} missing')
            continue
        task_data = database.get_task_history()[str(task_id)]
        for task_hist in task_data['taskHistory']:
            if task_hist['action'] == 'LOCKED_FOR_VALIDATION' or task_hist['action'] == 'LOCKED_FOR_MAPPING':
                datetime = pd.to_datetime(task_hist['actionDate'])
                year = datetime.year
                month = datetime.month
                day = datetime.day
                relative_day = (datetime.date() - start).days
                hour = datetime.hour
                minute = datetime.minute
                second = datetime.second

                date_duration = pd.to_datetime(task_hist['actionText'])
                duration = date_duration.second + 60 * date_duration.minute + 3600 * date_duration.hour

                author = task_hist['actionBy']

                type_action = task_hist['action'].split('_')[-1]

                raw_data = pd.concat([raw_data, pd.DataFrame(data=[(project, task_id, year, month, day, relative_day,
                                                                    hour, minute, second, duration, author, type_action)],
                                                             columns=['Project', 'Task', 'Year', 'Month', 'Day', 'Rel. Day',
                                                                      'Hour', 'Minute', 'Second', 'Duration', 'Author',
                                                                      'Type'])], axis=0)
    return raw_data


if __name__ == '__main__':
    args = get_args()
    project_id = args.project_id
    db = dm.Database(project_id)

    stats_dir = os.path.join(dm.get_data_dir(), 'stats')
    os.makedirs(stats_dir, exist_ok=True)
    csv_file = os.path.join(stats_dir, str(project_id) + '.csv')
    tasks_data = compute_task_data(db)
    tasks_data.to_csv(csv_file, index=None)
    print(f'Stats exported in {csv_file}')
