import argparse
import datetime
import os
import pandas as pd

import tasking_manager_stats.data_management as dm


def get_args():
    parser = argparse.ArgumentParser(description='Agregate users data from tasking manager API')
    parser.add_argument('merged_stats', type=str, help='Path of the merged stats CSV file')
    parser.add_argument('stats_one_author', type=str, help='Path of the merged stats 1 author by task type CSV file')
    parser.add_argument('mapathon', type=str, help='Path of the mapathon CSV file')
    parser.add_argument('-max_date', type=str, help='Date (%Y_%m_%d) to stop data and compute if contributor come back')
    return parser.parse_args()


def compute_mapathon_number(mapathon_file, stats_file, max_date=None):
    mapathons = pd.read_csv(mapathon_file)
    mapathons['Date'] = pd.to_datetime(mapathons['Date'], dayfirst=True)

    # Extract projects of the mapathon
    mapathons2 = pd.DataFrame()
    for _, row in mapathons.iterrows():
        tasks = row['Tasks']
        if pd.isnull(tasks):
            continue
        projects = set()
        for s in tasks.split('/'):
            try:
                projects.add(int(s))
            except:
                pass
        for s in tasks.split(', '):
            try:
                projects.add(int(s))
            except:
                pass
                # Create new mapathon line for each project
        for project in projects:
            mapathons2 = pd.concat([mapathons2, pd.DataFrame(data=[(row['Date'], row['City'], project)],
                                                             columns=['date', 'City', 'Project'])], axis=0,
                                   ignore_index=True)

    # Compute number of mapathons by contributor
    df = pd.read_csv(stats_file, encoding='ISO-8859-1')
    df['date'] = df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-' + df['Day'].astype(str)
    df['date'] = pd.to_datetime(df['date'], yearfirst=True)
    if max_date is not None:
        df = df[df['date'] <= max_date]
    df2 = df[(df['Hour'] > 17) & (df['Hour'] < 22)]
    df3 = pd.merge(df2.loc[df2['Type'] == 'MAPPING'], mapathons2, on=['date', 'Project'])
    df4 = df3[['date', 'Author', 'City', 'Project']].drop_duplicates()
    res = df4[['Author', 'date']].drop_duplicates().groupby('Author').count().date.reset_index()
    res.columns = ['Author', 'MapathonNb']
    return res


def compute_validation_time_by_task(stats_dir, csv_file, max_date=None):
    df_project = pd.read_csv(os.path.join(stats_dir, csv_file), encoding='ISO-8859-1')
    df_project = df_project[df_project['Type'] == 'VALIDATION']
    if len(df_project) == 0:
        return pd.DataFrame()
    if max_date is not None:
        df_project['date'] = df_project['Year'].astype(str) + '-' + df_project['Month'].astype(str) + '-' + df_project['Day'].astype(str)
        df_project['date'] = pd.to_datetime(df_project['date'], yearfirst=True)
        df_project = df_project[df_project['date'] <= max_date]
        if len(df_project) == 0:
            return pd.DataFrame()
    key = ['Year', 'Month', 'Day', 'Rel. Day', 'Hour', 'Minute', 'Second', 'Duration', 'Author', 'Type']
    df_project2 = df_project.groupby(key).count().Task
    df_project2 = df_project2.reset_index()
    df_project3 = pd.merge(df_project, df_project2, on=key)
    df_project3['Duration'] /= df_project3['Task_y']
    df_project3 = df_project3[['Project', 'Task_x', 'Duration']]
    df_project3.columns = ['Project', 'Task', 'Duration']
    df_project3 = df_project3.groupby(['Project', 'Task']).sum().reset_index()
    return df_project3


def compute_validation_time_by_task_all_projects(stats_dir, max_date=None):
    df = pd.DataFrame()
    for file in os.listdir(stats_dir):
        if file.endswith('.csv'):
            df = pd.concat([df, compute_validation_time_by_task(stats_dir, file, max_date)], axis=0, ignore_index=True)
    return df


def compute_advanced_stats(stats_dir, df_one_author, df, max_date=None):
    validation_df = compute_validation_time_by_task_all_projects(stats_dir, max_date)
    validation_df.columns = ['Project', 'Task', 'ValidationDuration']
    if max_date is not None:
        df_one_author['date'] = df_one_author['Year'].astype(int).astype(str) + '-' + df_one_author['Month'].astype(int).astype(str) + '-' + df_one_author['Day'].astype(int).astype(str)
        df_one_author['date'] = pd.to_datetime(df_one_author['date'], yearfirst=True)
        df_one_author = df_one_author[df_one_author['date'] <= max_date]
        del df_one_author['date']
        df = df[df['date'] <= max_date]
    df_mapping = pd.merge(validation_df, df_one_author[df_one_author['Type'] == 'MAPPING'], on=['Project', 'Task'])
    df_mapping_valid = df_mapping.groupby('Author').sum().ValidationDuration.reset_index()
    df_pure_mapping = df[df['Type'] == 'MAPPING'].groupby('Author').sum().Duration.reset_index()
    df_pure_mapping.columns = ['Author', 'OwnMappingDuration']
    res = pd.merge(df_pure_mapping, df_mapping_valid, on='Author', how='left')
    df_pure_validation = df[df['Type'] == 'VALIDATION'].groupby('Author').sum().Duration.reset_index()
    df_pure_validation.columns = ['Author', 'OwnValidationDuration']
    res = pd.merge(res, df_pure_validation, on='Author', how='left')
    res['ValidationOnOwnMappingDuration'] = res['ValidationDuration'] / res['OwnMappingDuration']
    return res


def aggregate_merged_stats(merged_stats, max_date=None):
    if max_date is not None:
        merged_stats = merged_stats[merged_stats['date'] <= max_date]
    df = merged_stats[['date', 'Author']].drop_duplicates()
    df = df.groupby('Author').count().date.reset_index()
    df.columns = ['Author', 'ContribDayNb']
    df2 = merged_stats.groupby('Author').min().date.reset_index()
    df2.columns = ['Author', 'FirstContrib']
    df = pd.merge(df, df2, on='Author')
    df3 = merged_stats.groupby('Author').max().date.reset_index()
    df3.columns = ['Author', 'LatestContrib']
    df = pd.merge(df, df3, on='Author')
    df4 = merged_stats[['Project', 'Author']].drop_duplicates()
    df4 = df4.groupby('Author').count().Project.reset_index()
    df4.columns = ['Author', 'ProjectNb']
    df = pd.merge(df, df4, on='Author')
    return df


def aggregate_merged_stats_one_author_by_task_type(merged_stats_one_author_by_task_type, max_date=None):
    if max_date is not None:
        merged_stats_one_author_by_task_type['date'] = merged_stats_one_author_by_task_type['Year'].astype(int).astype(str) + '-' + merged_stats_one_author_by_task_type['Month'].astype(int).astype(str) + '-' + merged_stats_one_author_by_task_type['Day'].astype(int).astype(str)
        merged_stats_one_author_by_task_type['date'] = pd.to_datetime(merged_stats_one_author_by_task_type['date'], yearfirst=True)
        merged_stats_one_author_by_task_type = merged_stats_one_author_by_task_type[merged_stats_one_author_by_task_type['date'] <= max_date]
        del merged_stats_one_author_by_task_type['date']
    df = merged_stats_one_author_by_task_type[merged_stats_one_author_by_task_type['Type'] == 'MAPPING']
    df = df.groupby('Author').count().Type.reset_index()
    df.columns = ['Author', 'MappingTaskNb']
    df2 = merged_stats_one_author_by_task_type[merged_stats_one_author_by_task_type['Type'] == 'VALIDATION']
    df2 = df2.groupby('Author').count().Type.reset_index()
    df2.columns = ['Author', 'ValidationTaskNb']
    df = pd.merge(df, df2, on='Author', how='left')
    return df


if __name__ == '__main__':
    args = get_args()
    max_date = datetime.datetime.strptime(args.max_date, '%Y_%m_%d') if args.max_date is not None else None
    merged_stats = pd.read_csv(args.merged_stats, encoding='ISO-8859-1')
    merged_stats['date'] = merged_stats['Year'].astype(str) + '-' + merged_stats['Month'].astype(str) + '-' + merged_stats['Day'].astype(str)
    merged_stats['date'] = pd.to_datetime(merged_stats['date'], yearfirst=True)
    user_stats = aggregate_merged_stats(merged_stats, max_date)
    merged_stats_one_author_by_task_type = pd.read_csv(args.stats_one_author, encoding='ISO-8859-1')
    user_stats2 = aggregate_merged_stats_one_author_by_task_type(merged_stats_one_author_by_task_type, max_date)
    user_stats = pd.merge(user_stats, user_stats2, on='Author')
    mapathon_stats = compute_mapathon_number(args.mapathon, args.merged_stats, max_date)
    user_stats = pd.merge(user_stats, mapathon_stats, on='Author', how='left')
    adv_stats = compute_advanced_stats(os.path.join(dm.get_data_dir(), 'stats'), merged_stats_one_author_by_task_type,
                                       merged_stats, max_date)
    user_stats = pd.merge(user_stats, adv_stats, on='Author', how='left')
    filename = 'agregated_user_stats.csv'
    if max_date is not None:
        come_back = merged_stats[merged_stats['date'] > max_date]['Author'].unique()
        come_back_df = pd.DataFrame(come_back, columns=['Author'])
        come_back_df['ComeBack'] = 1
        user_stats = pd.merge(user_stats, come_back_df, on='Author', how='left')
        filename = 'agregated_user_stats_' + args.max_date + '.csv'
    user_stats.to_csv(os.path.join(dm.get_data_dir(), filename), index=None)
    print(os.path.join(dm.get_data_dir(), filename) + ' successfully created')
