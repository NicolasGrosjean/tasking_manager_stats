import os
import argparse
from PIL import Image

import sys
sys.path.append(os.path.join(os.getcwd()))

import tasking_manager_stats.data_management as dm
import tasking_manager_stats.map_tools as map


def get_args():
    parser = argparse.ArgumentParser(description='Generate images of the map evolution')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    parser.add_argument('-ev', '--event_file', type=str, help='Path of the event CSV file')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    project_id = args.project_id
    event_file = args.event_file

    db = dm.Database(project_id)
    start = db.get_start_date()

    cartong_logo = Image.open(os.path.join(dm.get_data_dir(), 'CartONG_logo.png'))
    legend = Image.open(os.path.join(dm.get_data_dir(), 'Legend.png'))

    project_data_dir = os.path.join(dm.get_data_dir(), str(project_id))
    os.makedirs(project_data_dir, exist_ok=True)

    nb_days = map.compute_nb_days(db, start)
    tasks_states, locked_tasks = map.get_task_states_and_locked_tasks(db, start, nb_days)
    events = map.read_and_format_events(start, event_file)
    map.plot_and_save_project_maps(db, nb_days, start, tasks_states, locked_tasks, project_data_dir, cartong_logo,
                                   legend, events)

    contributors, validators = map.compute_contributors_validators(db)
    map.plot_and_save_credits(contributors, validators, project_data_dir)
    print('Done. All images generated !')
