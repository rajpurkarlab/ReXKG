import os
import json
import csv
import re
import pandas as pd
import numpy as np
from operator import itemgetter
from collections import OrderedDict, defaultdict

def has_measurement_units(text):
    # Use regex to match numbers followed by units, e.g., "8mm", "9cm", including ranges like "5-10mm"
    pattern = r'\d+(\.\d+)?\s*-?\s*(mm|cm|m|km|in|ft|yd|mi)'
    # Search for matching patterns in the text
    return bool(re.search(pattern, text))

def extract_size_relations(input_csv_file, input_json_file, save_csv_file):
    # Load entity data
    with open(input_json_file, 'r') as file:
        data = json.load(file)
    
    # Create a dictionary of entities with lowercase aliases as keys
    save_entity_dict = {}
    for idx, entity in data.items():
        for alias in entity['Aliases']:
            save_entity_dict[alias.lower()] = {
                'entity_type': entity['entity_type'],
                'count': entity['count'],
                'name': entity['Name'],
                'cui': entity['CUI']
            }
    
    # Load relation data
    relation_df = pd.read_csv(input_csv_file)
    
    # Process relations
    save_row = []
    for index, row in relation_df.iterrows():
        if has_measurement_units(row['source_entity']):
            try:
                target_entity = save_entity_dict[row['target_entity']]
                save_row.append([
                    row['source_entity'],
                    row['target_entity'],
                    target_entity['cui'],
                    target_entity['entity_type'],
                    row['count']
                ])
            except KeyError:
                print(f"Entity not found: {row['target_entity']}")
    
    # Save processed relations to CSV
    with open(save_csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['source_entity', 'target_entity', 'target_cui', 'target_entity_type', 'count'])
        writer.writerows(save_row)
    
    # Group by target_cui and aggregate
    df = pd.read_csv(save_csv_file)
    result = df.groupby('target_cui').agg({
        'source_entity': 'first',   # Keep the first occurrence of source_entity
        'target_entity': 'first',   # Keep the first occurrence of target_entity
        'target_entity_type': 'first',  # Keep the first occurrence of target_entity_type
        'count': 'sum'  # Sum the counts
    }).reset_index()
    
    # Save the final result
    result.to_csv(save_csv_file, index=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Extract Size Relations')
    parser.add_argument('--entity_dir', type=str, default='./entities')
    parser.add_argument('--real_dir', type=str, default='./relation')
    args = parser.parse_args()
    
    input_csv_file = os.path.join(args.real_dir, 'all_relations.csv')
    save_csv_file = os.path.join(args.real_dir, 'size_relations.csv')
    isolated_json_file = os.path.join(args.entity_dir, 'isolated_entities_merge.json')
    
    extract_size_relations(input_csv_file, isolated_json_file, save_csv_file)

