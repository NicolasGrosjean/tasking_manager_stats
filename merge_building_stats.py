import os
import pandas as pd
from tqdm import tqdm

import tasking_manager_stats.data_management as dm

"""
Merge all CSV files from data/buildings in to one.
Add BuildingsNbFromStart and Project columns.
"""
if __name__ == '__main__':
    buildings_dir = os.path.join(dm.get_data_dir(), 'buildings')
    stats = pd.DataFrame()
    for file in tqdm(os.listdir(buildings_dir)):
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(buildings_dir, file))
            df['BuildingDailyDiff'] = (df['BuildingNb'] - df['BuildingNb'].shift(1).fillna(0)).astype(int)
            df['Project'] = file[:-4]
            stats = pd.concat([stats, df], axis=0)
    dates = pd.to_datetime(stats['Date'], format='%Y-%m-%d').dt
    stats['Year'] = dates.year
    stats['Month'] = dates.month
    stats['Day'] = dates.day
    del stats['Date']
    stats.to_csv(os.path.join(dm.get_data_dir(), 'merged_building_stats.csv'), index=None)
