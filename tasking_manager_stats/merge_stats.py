import os
import pandas as pd

import tasking_manager_stats.data_management as dm

if __name__ == '__main__':
    stats_dir = os.path.join(dm.get_data_dir(), 'stats')
    stats = pd.DataFrame()
    for file in os.listdir(stats_dir):
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(stats_dir, file), encoding='ISO-8859-1')
            stats = pd.concat([stats, df], axis=0)
    stats['Duration'] = stats['Duration'].fillna(0)
    stats.loc[stats['Duration'] > 7200, 'Duration'] = 7200
    stats['Duration'] = stats['Duration'].astype(int)
    stats.loc[stats['Author'] == 'Jean-Yves Longchamp', 'Author'] = 'JYL45'
    stats.to_csv(os.path.join(dm.get_data_dir(), 'merged_stats.csv'), index=None)
    stats_agg1 = stats.groupby(['Author', 'Type']).sum()['Duration']
    stats_agg2 = stats.groupby(['Author', 'Type']).count()['Task']
    stats_agg = pd.DataFrame(stats_agg1).join(stats_agg2)
    stats_agg.columns= ['Duration_s', 'Nb_Tasks']
    stats_agg['Duration_h'] = stats_agg['Duration_s'] / 3600
    stats_agg.reset_index().to_csv(os.path.join(dm.get_data_dir(), 'merged_stats_agg.csv'), index=None)
