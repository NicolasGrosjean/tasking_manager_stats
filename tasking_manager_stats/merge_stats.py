import os
import pandas as pd

import tasking_manager_stats.data_management as dm

if __name__ == '__main__':
    stats_dir = os.path.join(dm.get_data_dir(), 'stats')
    stats = pd.DataFrame()
    for file in os.listdir(stats_dir):
        df = pd.read_csv(os.path.join(stats_dir, file), encoding='ISO-8859-1')
        stats = pd.concat([stats, df], axis=0)
    stats.to_csv(os.path.join(dm.get_data_dir(), 'merged_stats.csv'), index=None)
