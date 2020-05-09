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
    url = 'https://tasking-manager-tm4-production-api.hotosm.org/api/v2/projects/' + str(project_id)
    r = requests.get(url, headers=get_json_request_header())
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
    url = 'https://tasking-manager-tm4-production-api.hotosm.org/api/v2/projects/' + str(project_id) + '/queries/summary'
    r = requests.get(url, headers=get_json_request_header())
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
        url = 'https://tasking-manager-tm4-production-api.hotosm.org/api/v2/projects/' + str(project_id) + '/tasks/' + str(task_id)
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


def need_to_download_data(data_file_path, project_id):
    """
    Return if the data need do be downloaded. The cases to decide to download are:
    - The data has never been downloaded
    - The data has been downloaded in the latest 24h
    - The project has not been archived when the data has been downloaded the latest time
    :param data_file_path:
    :param project_id:
    :return:
    """
    if not os.path.exists(data_file_path):
        try:
            r = requests.get('https://raw.githubusercontent.com/NicolasGrosjean/tasking_manager_stats/master/data/json/' +
                             str(project_id) + '.json')
            with open(data_file_path, 'w') as outfile:
                json.dump(r.json(), outfile)
            print('Data file not found locally but found on GitHub, it has been downloaded from GitHub.')
        except Exception:
            print('Data file not found locally and on GitHub, it will be downloaded again.')
            return True
    elif (datetime.datetime.now().timestamp() - os.path.getmtime(data_file_path)) < 24 * 3600:
        print('Data downloaded in the latest 24h. It won\'t be downloaded again.')
        return False
    with open(data_file_path) as f:
        project_data = json.load(f)
    summary_data = download_summary_data(project_id)
    latest_update = pd.to_datetime(summary_data['lastUpdated'])
    latest_downloaded_update = pd.to_datetime(project_data['lastUpdated'])
    if latest_update > latest_downloaded_update:
        print(f'The project has been updated ({latest_update}) since the latest change downloaded ({latest_downloaded_update}), '
              f'it will be downloaded again from the HOT Tasking Manager.')
        return True
    print('Data file found and the project has not been changed. It won\'t be downloaded again.')
    return False


class Database:
    """
    The Database class manage the loading of the data and if necessary the downloading and the storage
    """
    def __init__(self, project_id, force_json_reading=False):
        os.makedirs(os.path.join(get_data_dir(), 'json'), exist_ok=True)
        data_file_path = os.path.join(get_data_dir(), 'json', str(project_id) + '.json')
        if not force_json_reading and need_to_download_data(data_file_path, project_id):
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

    def get_perimeter_poly(self):
        return self.project_data['areaOfInterest']

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

    def get_creation_date(self, date_format='%Y-%m-%d'):
        try:
            creation_datetime = datetime.datetime.strptime(self.project_data['created'], '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            creation_datetime = datetime.datetime.strptime(self.project_data['created'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return creation_datetime.strftime(date_format)

    def compute_final_validation_date(self, date_format='%Y-%m-%d'):
        final_date = pd.to_datetime('1970-01-01').date()
        for task_id in self.get_task_ids():
            if str(task_id) not in self.get_task_history():
                print(f'Task {task_id} missing')
                continue
            task_data = self.get_task_history()[str(task_id)]
            for task_hist in task_data['taskHistory']:
                if task_hist['actionText'] == 'VALIDATED' and task_hist['action'] == 'STATE_CHANGE':
                    date = pd.to_datetime(task_hist['actionDate']).date()
                    if date > final_date:
                        final_date = date
        return final_date.strftime(date_format)


if __name__ == '__main__':
    project_id = 5654
    Database(project_id)
