import argparse
import datetime
import math
import numpy as np
import os
import pandas as pd
import plotly.graph_objects as go


import sys
sys.path.append(os.path.join(os.getcwd()))
import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Generate images of the map evolution')
    parser.add_argument('project_id', type=int, help='Id of the HOT tasking manager project')
    parser.add_argument('date', type=str, help='Date of the mapathon')
    return parser.parse_args()


def generate_timestamps(date):
    start_date = datetime.datetime.strptime(date + ' 18:00:00', '%Y-%m-%d %H:%M:%S')
    start_date -= datetime.timedelta(hours=1)  # Winter
    return pd.date_range(start_date, start_date + datetime.timedelta(hours=2), freq='5min')


def compute_task_states(task_data, timestamps):
    task_states = np.zeros(len(timestamps))
    task_locked = np.zeros(len(timestamps))
    for task_hist in reversed(task_data['taskHistory']):
        date = pd.to_datetime(task_hist['actionDate'])
        if task_hist['action'].startswith('LOCK'):
            task_locked[date < timestamps] = 1
            task_locked[date + pd.to_timedelta(task_hist['actionText']) < timestamps] = 0
            continue
        if task_hist['action'] != 'STATE_CHANGE':
            continue
        if task_hist['actionText'] == 'MAPPED':
            task_states[date < timestamps] = 1
            continue
        if task_hist['actionText'] == 'INVALIDATED':
            task_states[date < timestamps] = 2
            continue
        if task_hist['actionText'] == 'VALIDATED':
            task_states[date < timestamps] = 3
            continue
        if task_hist['actionText'] == 'BADIMAGERY':
            task_states[date < timestamps] = 4
            continue
    return task_states, task_locked


def get_task_states_and_locked_tasks(db, timestamps):
    tasks_states = dict()
    tasks_locked = dict()
    for task_id in db.get_task_ids():
        task_states, task_locked = compute_task_states(db.get_task_history()[str(task_id)], timestamps)
        tasks_states[task_id] = task_states
        tasks_locked[task_id] = task_locked
    return tasks_states, tasks_locked


def plot_lock(fig, xmin, xmax, ymin, ymax):
    delta_x = xmax - xmin
    delta_y = ymax - ymin
    # Big Rectangle
    fig.add_trace(go.Scatter(x=[xmin + 0.2 * delta_x, xmin + 0.8 * delta_x,
                                xmin + 0.8 * delta_x, xmin + 0.2 * delta_x],
                             y=[ymin + 0.15 * delta_y, ymin + 0.15 * delta_y,
                                ymin + 0.55 * delta_y, ymin + 0.55 * delta_y],
                             marker=dict(color='#2C3038'), mode='lines', fill='toself', fillcolor='#2C3038', name=''))

    # Small rectangles
    fig.add_trace(go.Scatter(x=[xmin + 0.35 * delta_x, xmin + 0.4 * delta_x,
                                xmin + 0.4 * delta_x, xmin + 0.35 * delta_x],
                             y=[ymin + 0.55 * delta_y, ymin + 0.55 * delta_y,
                                ymin + 0.7 * delta_y, ymin + 0.7 * delta_y],
                             marker=dict(color='#2C3038'), mode='lines', fill='toself', fillcolor='#2C3038', name=''))
    fig.add_trace(go.Scatter(x=[xmin + 0.6 * delta_x, xmin + 0.65 * delta_x,
                                xmin + 0.65 * delta_x, xmin + 0.6 * delta_x],
                             y=[ymin + 0.55 * delta_y, ymin + 0.55 * delta_y,
                                ymin + 0.7 * delta_y, ymin + 0.7 * delta_y],
                             marker=dict(color='#2C3038'), mode='lines', fill='toself', fillcolor='#2C3038', name=''))

    # Half Circle
    point_nb = 20
    th = np.arange(-math.pi / 2, math.pi / 2 + math.pi / (2 * point_nb), math.pi / (point_nb - 1))
    x = np.empty(2 * point_nb)
    y = np.empty(2 * point_nb)
    x[:point_nb] = 0.1 * delta_x * np.sin(th) + 0.5 * delta_x + xmin
    y[:point_nb] = 0.075 * delta_y * np.cos(th) + 0.7 * delta_y + ymin
    x[point_nb:] = 0.15 * delta_x * np.sin(-th) + 0.5 * delta_x + xmin
    y[point_nb:] = 0.12 * delta_y * np.cos(-th) + 0.7 * delta_y + ymin
    fig.add_trace(go.Scatter(x=x, y=y, marker=dict(color='#2C3038'), mode='lines', fill='toself',
                             fillcolor='#2C3038', name=''))


def get_lock_dicts(xmin, xmax, ymin, ymax, color='#2C3038'):
    delta_x = xmax - xmin
    delta_y = ymax - ymin
    # Big Rectangle
    dict1 = dict(x=[xmin + 0.2 * delta_x, xmin + 0.8 * delta_x, xmin + 0.8 * delta_x, xmin + 0.2 * delta_x],
                 y=[ymin + 0.15 * delta_y, ymin + 0.15 * delta_y, ymin + 0.55 * delta_y, ymin + 0.55 * delta_y],
                 marker=dict(color=color), mode='lines', fill='toself', fillcolor=color, name='')

    # Small rectangles
    dict2 = dict(x=[xmin + 0.35 * delta_x, xmin + 0.4 * delta_x, xmin + 0.4 * delta_x, xmin + 0.35 * delta_x],
                 y=[ymin + 0.55 * delta_y, ymin + 0.55 * delta_y, ymin + 0.7 * delta_y, ymin + 0.7 * delta_y],
                 marker=dict(color=color), mode='lines', fill='toself', fillcolor=color, name='')
    dict3 = dict(x=[xmin + 0.6 * delta_x, xmin + 0.65 * delta_x, xmin + 0.65 * delta_x, xmin + 0.6 * delta_x],
                 y=[ymin + 0.55 * delta_y, ymin + 0.55 * delta_y, ymin + 0.7 * delta_y, ymin + 0.7 * delta_y],
                 marker=dict(color=color), mode='lines', fill='toself', fillcolor=color, name='')

    # Half Circle
    point_nb = 20
    th = np.arange(-math.pi / 2, math.pi / 2 + math.pi / (2 * point_nb), math.pi / (point_nb - 1))
    x = np.empty(2 * point_nb)
    y = np.empty(2 * point_nb)
    x[:point_nb] = 0.1 * delta_x * np.sin(th) + 0.5 * delta_x + xmin
    y[:point_nb] = 0.075 * delta_y * np.cos(th) + 0.7 * delta_y + ymin
    x[point_nb:] = 0.15 * delta_x * np.sin(-th) + 0.5 * delta_x + xmin
    y[point_nb:] = 0.12 * delta_y * np.cos(-th) + 0.7 * delta_y + ymin
    dict4 = dict(x=x, y=y, marker=dict(color=color), mode='lines', fill='toself', fillcolor=color, name='')

    return dict1, dict2, dict3, dict4


def compute_and_export_animation(timestamps, project_id, tasks_states, tasks_locked):
    timestamps_paris = timestamps.tz_localize('utc').tz_convert('Europe/Paris')
    date = datetime.datetime.strftime(timestamps_paris[0], '%Y-%m-%d')
    fig_dict = dict(data=[], layout={}, frames=[])
    fig_dict['layout'] = dict(showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
                              xaxis=dict(visible=False), yaxis=dict(visible=False),
                              title=dict(text=f'{db.get_project_name()} #{project_id}<br>Mapathon date : {date}'))
    fig_dict['layout']['updatemenus'] = [
        {
            'buttons': [
                {
                    'args': [None, {'frame': {'duration': 500, 'redraw': False},
                                    'fromcurrent': True, 'transition': {'duration': 0,
                                                                        'easing': 'quadratic-in-out'}}],
                    'label': 'Play',
                    'method': 'animate'
                },
                {
                    'args': [[None], {'frame': {'duration': 0, 'redraw': False},
                                      'mode': 'immediate',
                                      'transition': {'duration': 0}}],
                    'label': 'Pause',
                    'method': 'animate'
                }
            ],
            'direction': 'left',
            'pad': {'r': 10, 't': 87},
            'showactive': False,
            'type': 'buttons',
            'x': 0.1,
            'xanchor': 'right',
            'y': 0,
            'yanchor': 'top'
        }
    ]

    sliders_dict = {
        'active': 0,
        'yanchor': 'top',
        'xanchor': 'left',
        'currentvalue': {
            'font': {'size': 20},
            'visible': True,
            'xanchor': 'right'
        },
        'transition': {'duration': 300, 'easing': 'cubic-in-out'},
        'pad': {'b': 10, 't': 50},
        'len': 0.9,
        'x': 0.1,
        'y': 0,
        'steps': []
    }

    # for time_id in range(int(len(timestamps)/4)):
    for time_id in range(len(timestamps)):
        hour = datetime.datetime.strftime(timestamps_paris[time_id], '%Hh%M')
        frame = {'data': [], 'name': hour}
        for feature in db.get_task_features():
            arr = np.array(feature['geometry']['coordinates'][0][0]).transpose()
            task_id = feature['properties']['taskId']
            state = tasks_states[task_id][time_id]
            if state == 1:  # MAPPED
                data_dict = dict(x=arr[0], y=arr[1], marker=dict(color='#ADE6EF'), mode='lines', fill='toself', name='')
                frame['data'].append(data_dict)
                if time_id == 0:
                    fig_dict['data'].append(data_dict)
            elif state == 2:  # INVALIDATED
                data_dict = dict(x=arr[0], y=arr[1], marker=dict(color='#FCECA4'), mode='lines', fill='toself', name='')
                frame['data'].append(data_dict)
                if time_id == 0:
                    fig_dict['data'].append(data_dict)
            elif state == 3:  # VALIDATED
                data_dict = dict(x=arr[0], y=arr[1], marker=dict(color='#40AC8C'), mode='lines', fill='toself', name='')
                frame['data'].append(data_dict)
                if time_id == 0:
                    fig_dict['data'].append(data_dict)
            elif state == 4:  # BADIMAGERY
                data_dict = dict(x=arr[0], y=arr[1], marker=dict(color='#D8DAE4'), mode='lines', fill='toself', name='')
                frame['data'].append(data_dict)
                if time_id == 0:
                    fig_dict['data'].append(data_dict)
            else:
                data_dict = dict(x=arr[0], y=arr[1], marker=dict(color='#FFFFFF'), mode='lines', fill='toself', name='')
                frame['data'].append(data_dict)
                if time_id == 0:
                    fig_dict['data'].append(data_dict)
            # Add lock if there is one
            if tasks_locked[task_id][time_id] == 1:
                lock_dicts = get_lock_dicts(arr[0].min(), arr[0].max(), arr[1].min(), arr[1].max())
                for lock_dict in lock_dicts:
                    frame['data'].append(lock_dict)
                    if time_id == 0:
                        fig_dict['data'].append(lock_dict)
            else:
                lock_dicts = get_lock_dicts(arr[0].min(), arr[0].max(), arr[1].min(), arr[1].max(),
                                            color='rgba(0,0,0,0)')
                for lock_dict in lock_dicts:
                    frame['data'].append(lock_dict)
                    if time_id == 0:
                        fig_dict['data'].append(lock_dict)

        # Plot borders
        for feature in db.get_task_features():
            arr = np.array(feature['geometry']['coordinates'][0][0]).transpose()
            data_dict = dict(x=arr[0], y=arr[1], marker=dict(color='#999DB5'), mode='lines', name='')
            frame['data'].append(data_dict)
            if time_id == 0:
                fig_dict['data'].append(data_dict)
        fig_dict['frames'].append(frame)
        slider_step = dict(args=[[hour],
                                 {'frame': {'duration': 1000, 'redraw': False},
                                  'mode': 'immediate', 'transition': {'duration': 0}}],
                           label=hour, method='animate')
        sliders_dict['steps'].append(slider_step)

    fig_dict['layout']['sliders'] = [sliders_dict]

    fig = go.Figure(fig_dict)
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=50), hovermode=False)
    date = datetime.datetime.strftime(timestamps_paris[0], '%Y-%m-%d')
    file_name = f'mapathon_{project_id}_{date}.json'
    with open(os.path.join(dm.get_data_dir(), file_name), 'w') as f:
        f.write(fig.to_json())
    print(f'{file_name} created!')


if __name__ == '__main__':
    args = get_args()
    timestamps = generate_timestamps(args.date)
    db = dm.Database(args.project_id)
    tasks_states, tasks_locked = get_task_states_and_locked_tasks(db, timestamps)
    compute_and_export_animation(timestamps, args.project_id, tasks_states, tasks_locked)
