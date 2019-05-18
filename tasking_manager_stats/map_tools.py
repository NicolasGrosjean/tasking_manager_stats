import os
import math
from tqdm import tqdm
import textwrap
from PIL import Image
import numpy as np
import pandas as pd
import matplotlib.patches as patches
import matplotlib.pyplot as plt


def compute_nb_days(db, start):
    """
    Compute the number of days of the project (days between start and the date of the last action)
    :param db:
    :param start:
    :return:
    """
    nb_days = 0
    for task_id in db.get_task_ids():
        date = pd.to_datetime(db.get_task_history()[str(task_id)]['taskHistory'][0]['actionDate']).date()
        day = (date - start).days
        nb_days = max(nb_days, day)
    return nb_days


def get_task_states(task_data, locked_tasks, start, nb_days):
    """
    Processed each history of a task to fill locked_tasks and return states.
    
    Return a numpy array indexed by days from start with the following values
    * 0 : NOTHING
    * 1 : MAPPED
    * 2 : INVALIDATED
    * 3 : VALIDATED
    * 4 : BADIMAGERY
    """
    task_states = np.zeros(nb_days + 1)
    for task_hist in reversed(task_data['taskHistory']):
        date = pd.to_datetime(task_hist['actionDate']).date()
        day = (date - start).days
        if task_hist['action'].startswith('LOCK'):
            locked_tasks[day].add(task_data['taskId'])
            continue
        if task_hist['action'] != 'STATE_CHANGE':
            continue
        if task_hist['actionText'] == 'MAPPED':
            task_states[day:] = 1
            continue
        if task_hist['actionText'] == 'INVALIDATED':
            task_states[day:] = 2
            continue
        if task_hist['actionText'] == 'VALIDATED':
            task_states[day:] = 3
            continue
        if task_hist['actionText'] == 'BADIMAGERY':
            task_states[day:] = 4
            continue
    return task_states


def get_task_states_and_locked_tasks(db, start, nb_days):
    """
    Retrun tasks_states a dictionary with key a task_id and value an array given the task state for each day,
    and locked_tasks a list given the set of locked tasks for each day
    :param db:
    :param nb_days:
    :return:
    """
    locked_tasks = []
    for i in range(nb_days + 1):
        locked_tasks.append(set())
    tasks_states = dict()
    for task_id in db.get_task_ids():
        tasks_states[task_id] = get_task_states(db.get_task_history()[str(task_id)], locked_tasks, start, nb_days)
    return tasks_states, locked_tasks


def add_contributor(task_data, contributors, validators):
    for task_hist in task_data['taskHistory']:
        contributors.add(task_hist['actionBy'])
        if task_hist['actionText'] == 'VALIDATED':
            validators.add(task_hist['actionBy'])


def compute_contributors_validators(db):
    """
    Compute the list (alphabetically sorted) of contributors and a set of validators
    :param db:
    :return:
    """
    contributors = set()
    validators = set()
    for task_id in db.get_task_ids():
        add_contributor(db.get_task_history()[str(task_id)], contributors, validators)
    contributors = list(contributors)
    contributors.sort(key=lambda v: v.upper())
    return contributors, validators


def read_and_format_events(start, event_file):
    """
    Read an event file and return a formatted DataFRame
    :param start:
    :param event_file:
    :return:
    """
    events = pd.read_csv(event_file)
    events['date'] = pd.to_datetime(events['date'])
    events['days'] = events['date'].apply(lambda date: (date.date() - start).days)
    return events.set_index('days')


def plot_and_save_project_maps(db, nb_days, start, tasks_states, locked_tasks, project_data_dir, cartong_logo, legend,
                               events):
    """
    Plot and for each day the map with locked task and the map with the states changed

    :param db: Database of the project
    :param nb_days: Number of days of the project (there will 2*nb_days images)
    :param start: Start date of the project
    :param tasks_states: Dictionary of a list of task state for day, indexed by task id
    :param locked_tasks: List given the set of locked tasks for each day
    :param project_data_dir: Directory of the project in which images will be saved
    :param cartong_logo: Image of the CartONG logo displayed in top and left of each image
    :param legend: Image of the legend displayed in bottom and left of each image
    :param events: Dataframe of the events to add in the title
    :return:
    """
    print('Plot and save project maps')
    for day in tqdm(range(nb_days + 1)):
        for plot_lock in [True, False]:
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 10), dpi=100, sharex=True)

            for feature in db.get_task_features():
                # Plot borders
                arr = np.array(feature['geometry']['coordinates'][0][0]).transpose()
                plt.plot(arr[0], arr[1], color='black')

                # Plot locking or state
                task_id = feature['properties']['taskId']
                state = tasks_states[task_id][day]
                if plot_lock and task_id in locked_tasks[day]:
                    ax.add_patch(patches.Polygon(arr.transpose(), color=(159/255., 188/255., 247/255.)))  # blue
                    continue
                if state == 1:
                    ax.add_patch(patches.Polygon(arr.transpose(), color=(254/255., 231/255., 156/255.)))  # yellow
                    continue
                if state == 2:
                    ax.add_patch(patches.Polygon(arr.transpose(), color=(245/255., 156/255., 178/255.)))  # pink
                    continue
                if state == 3:
                    ax.add_patch(patches.Polygon(arr.transpose(), color=(152/255., 203/255., 151/255.)))  # green
                    continue
                if state == 4:
                    ax.add_patch(patches.Polygon(arr.transpose(), color=(152/255., 152/255., 151/255.)))  # black
                    continue

            # Plot priority area
            if db.get_priority_area() is not None:
                for priority_area in db.get_priority_area():
                    ax.add_patch(patches.Polygon(priority_area['coordinates'][0], fill=False, color='r', lw=2))

            str_day_title = (start + pd.Timedelta(days=day)).strftime('%d-%m-%Y')
            if events is not None and day in events.index:
                str_day_title = str_day_title + ' ' + events.loc[day, 'event']
            project_id = db.get_project_id()
            title = '\n'.join(textwrap.wrap(db.get_project_name() + ' #' + str(project_id), 50)) + '\n' + str_day_title
            ax.set_title(title, fontsize=16)
            ax.axis('off')

            # Same scale in both axis
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            xscale = xlim[1] - xlim[0]
            yscale = ylim[1] - ylim[0]
            if xscale > yscale:
                ax.set_ylim([ylim[0] - (xscale - yscale) / 2, ylim[1] + (xscale - yscale) / 2])
            else:
                ax.set_xlim([xlim[0] - (yscale - xscale) / 2, xlim[1] + (yscale - xscale) / 2])

            # Save plot
            str_day_file = (start + pd.Timedelta(days=day)).strftime('%Y-%m-%d')
            suffix = '_2' if not plot_lock else ''
            file_path = os.path.join(project_data_dir, str_day_file + suffix + '.png')
            plt.savefig(file_path, dpi=100)
            plt.close()

            # Add CartONG logo
            im = Image.open(file_path)
            im.paste(cartong_logo, (0, 0))
            im.paste(legend, (0, 1000-legend.size[1]))
            im.save(file_path)


def plot_and_save_credits(contributors, validators, project_data_dir):
    """
    Plot and save an image (project_data_dir/contributors.png) listing the contributors and validators
    :param contributors:
    :param validators:
    :param project_data_dir:
    :return:
    """
    max_y = 0.95
    step_y = 0.025
    max_nb_y = round(max_y/step_y) + 1
    max_x = 0.95
    step_x = max_x / max((math.ceil(len(contributors) / max_nb_y) - 1), 1)

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 10), dpi=100, sharex=True)
    for i in range(len(contributors)):
        color = 'g' if contributors[i] in validators else 'black'
        ax.text(int(i / max_nb_y) * step_x, max_y - (i % max_nb_y) * step_y, contributors[i], color=color)

    ax.set_title('Thanks to contributors and', fontsize=16)
    ax.text(0.7, 1.012, 'validators', fontsize=16, color='g')
    ax.axis('off')

    file_path = os.path.join(project_data_dir, 'contributors.png')
    plt.savefig(file_path, dpi=100)
