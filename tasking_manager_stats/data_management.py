import os
import json
import time
import datetime
import random
from tqdm import tqdm
import requests
import pandas as pd


def get_json_request_header():
    """
    Return the header for JSON request
    :return:
    """
    return {'Accept': 'application/json', 'Authorization': 'Token sessionTokenHere==', 'Accept-Language': 'en'}


def get_data_dir():
    """
    Get the path of the data directory
    :return:
    """
    if os.path.exists('data'):
        return 'data'
    elif os.path.join('..', 'data'):
        return os.path.join('..', 'data')
    raise Exception('Data directory not found')


def download_project_data(project_id):
    """
    Download the project data of the HOT tasking manager project id
    :param project_id:
    :return:
    """
    url = 'https://tasks.hotosm.org/api/v1/project/' + str(project_id)
    r = requests.get(url, headers=get_json_request_header())
    # TODO Manage error cases ?
    return r.json()


def extract_task_ids(project_data):
    """
    Extract from project data the list of task id
    :param project_data: Dictionary of project data of a HOT tasking manager project
    :return:
    """
    tasks_ids = list()
    for feature in project_data['tasks']['features']:
        tasks_ids.append(feature['properties']['taskId'])
    return tasks_ids


def download_summary_data(project_id):
    """
    Download the summary data of the HOT tasking manager project id
    :param project_id:
    :return:
    """
    url = 'https://tasks.hotosm.org/api/v1/project/' + str(project_id) + '/summary'
    r = requests.get(url, headers=get_json_request_header())
    # TODO Manage error cases ?
    return r.json()


def add_summary_data(project_data, summary_data):
    """
    Add key/values of summary_data dictionary to project_data dictionary
    :param project_data:
    :param summary_data:
    :return:
    """
    for key in summary_data:
        if key not in project_data.keys():
            project_data[key] = summary_data[key]


def download_and_add_task_history_data(project_data, project_id):
    """
    Download the history of each task and store it in project_data
    :param project_data: Dictionary in which will be store task list (key : task_ids) and history (key : task_history)
    :return:
    """
    project_data['tasks_ids'] = extract_task_ids(project_data)
    task_history = dict()
    missing_tasks = list()
    print('Download tasking manager data for project ' + str(project_id))
    for task_id in tqdm(project_data['tasks_ids']):
        url = 'https://tasks.hotosm.org/api/v1/project/' + str(project_id) + '/task/' + str(task_id)
        r = requests.get(url, headers=get_json_request_header())
        if r.ok:
            task_history[str(task_id)] = r.json()
        else:
            missing_tasks.append(task_id)
        time.sleep(0.5 + random.random())
    if len(missing_tasks) > 0:
        print(f'{len(missing_tasks)} missing tasks')
        # TODO Try to download missing tasks
    project_data['task_history'] = task_history


def store_project_data(project_data, json_file_path):
    """
    Store project_data in a JSON file (json_file_path)
    :param project_data:
    :param json_file_path:
    :return:
    """
    with open(json_file_path, 'w') as outfile:
        json.dump(project_data, outfile)


def need_to_download_data(data_file_path):
    """
    Return if the data need do be downloaded. The cases to decide to download are:
    - The data has never been downloaded
    - The data has been downloaded in the latest 24h
    - The project has not been archived when the data has been downloaded the latest time
    :param data_file_path:
    :return:
    """
    if not os.path.exists(data_file_path):
        print('Data file not found, it will be downloaded again.')
        return True
    if (datetime.datetime.now().timestamp() - os.path.getmtime(data_file_path)) < 24 * 3600:
        print('Data downloaded in the latest 24h. It won\'t be downloaded again.')
        return False
    with open(data_file_path) as f:
        project_data = json.load(f)
    if project_data['status'] != 'ARCHIVED':
        print('Data downloaded when the project hasn\'t been archived. It will be downloaded again.')
        # TODO : Ask user if he wants downloading data or not
        return True
    print('Data file found and the project is archived. It won\'t be downloaded again.')
    return False


class Database:
    """
    The Database class manage the loading of the data and if necessary the downloading and the storage
    """
    def __init__(self, project_id):
        data_file_path = os.path.join(get_data_dir(), str(project_id) + '.json')
        if need_to_download_data(data_file_path):
            self.project_data = download_project_data(project_id)
            summary_data = download_summary_data(project_id)
            add_summary_data(self.project_data, summary_data)
            download_and_add_task_history_data(self.project_data, project_id)
            store_project_data(self.project_data, data_file_path)
        else:
            with open(data_file_path) as f:
                self.project_data = json.load(f)

    def get_priority_area(self):
        return self.project_data['priorityAreas']

    def get_start_date(self):
        return pd.to_datetime(self.project_data['created']).date()

    def get_task_history(self):
        return self.project_data['task_history']

    def get_task_ids(self):
        return self.project_data['tasks_ids']

    def get_task_features(self):
        return self.project_data['tasks']['features']

    def get_project_name(self):
        return self.project_data['name']

    def get_project_center_coordinates(self):
        return self.project_data['aoiCentroid']['coordinates']

    def get_project_id(self):
        return self.project_data['projectId']


if __name__ == '__main__':
    project_id = 5654
    Database(project_id)
