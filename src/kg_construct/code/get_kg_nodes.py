import os 
import csv
import json 

import numpy as np
import pandas as pd 
from tqdm import tqdm

def get_kg_nodes(input_isolated_entities_json,save_kg_nodes_json):
    # Read the original JSON file
    with open(input_isolated_entities_json, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Initialize the transformed data dictionary
    transformed_data = {}
    idx = 0  # Index for new key

    # Iterate through the original data and transform it
    for key, value in data.items():
        # new_key = f"ISOENT{idx:04d}"  # Generate new key like ISOENT0000, ISOENT0001, ...
        # transformed_data[new_key] 
        save_transformed_data = value
        new_key = value['CUI'] 
        if value['CUI'] == "":
            new_key = value['Aliases'][0]
            save_transformed_data['CUI'] = value['Aliases'][0]
        if value['Name'] == "":
            save_transformed_data['Name'] = value['Aliases'][0]
        transformed_data[new_key] = save_transformed_data   
        transformed_data[new_key]['entity_type'] = value['entity_type']
        idx += 1

    # Write the transformed data to a new JSON file
    with open(save_kg_nodes_json, 'w', encoding='utf-8') as file:
        json.dump(transformed_data, file, indent=4, ensure_ascii=False)

def get_kg_subgraphs(input_composed_entities_json,save_kg_nodes_json,save_kg_subgraphs_json):
    # Read the original JSON file
    save_kg_nodes_dict = {}
    with open(save_kg_nodes_json, 'r', encoding='utf-8') as file:
        kg_nodes_data = json.load(file)
    for key, value in kg_nodes_data.items():
        save_kg_nodes_dict[value['CUI']]=key
    
    transformed_data = {}
    with open(input_composed_entities_json, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
    for key, value in data.items():
        cui_list = value["cui_list"]
        new_idx_list = []
        for cui in cui_list:
            new_idx_list.append(save_kg_nodes_dict[cui])
        new_key = ''.join(sorted(new_idx_list))
        transformed_data[new_key] = value
        transformed_data[new_key]["composed_cui"] = key
    
    # Write the transformed data to a new JSON file
    with open(save_kg_subgraphs_json, 'w', encoding='utf-8') as file:
        json.dump(transformed_data, file, indent=4, ensure_ascii=False)

def get_kg_relations(kg_nodes_json,kg_subgraphs_json,relation_csv,save_kg_relation_csv):
    save_node_idx_dict = {}
    with open(kg_nodes_json, 'r', encoding='utf-8') as file:
        kg_nodes_data = json.load(file)
    for key, value in kg_nodes_data.items():
        aliases_list = value['Aliases']
        aliases_list = [alias.lower() for alias in aliases_list]
        for alias in aliases_list:
            save_node_idx_dict[alias] = key
            
    with open(kg_subgraphs_json, 'r', encoding='utf-8') as file:
        kg_subgraphs_data = json.load(file)
    
    for key, value in kg_subgraphs_data.items():
        aliases_list = value['composed_entities']
        aliases_list = [alias.lower() for alias in aliases_list]
        for alias in aliases_list:
            save_node_idx_dict[alias] = key
    
    relation_df = pd.read_csv(relation_csv)
    # 创建新列，映射source_entity和target_entity到它们的索引
    relation_df['source_index'] = relation_df['source_entity'].map(save_node_idx_dict)
    relation_df['target_index'] = relation_df['target_entity'].map(save_node_idx_dict)

    # 合并相同source_index和target_index的行，叠加count列
    grouped_df = relation_df.groupby(['source_index', 'target_index']).agg({
        'source_entity': 'first',  # 可以根据需要保留其他列
        'target_entity': 'first',
        'type': 'first',  # 假设type在这些行中是相同的，如果不是，需要另外处理
        'count': 'sum'
    }).reset_index()
    
    grouped_df.dropna(subset=['source_index', 'target_index'], inplace=True)

    # 根据count列进行排序，降序
    sorted_df = grouped_df.sort_values(by='count', ascending=False)
    # 保存修改后的DataFrame到新的CSV文件
    sorted_df.to_csv(save_kg_relation_csv, index=False)

def keep_most_frequent_relation(relation_csv):
    df = pd.read_csv(relation_csv)
    # Initialize 'delete' column to False for all rows
    df['delete'] = False
    # A dictionary to store the indices where sums need to be added
    index_map = {}

    # Iterate through the DataFrame
    for index, row in df.iterrows():
        reversed_pair = (row['target_index'], row['source_index'])

        # Check if reversed pair already encountered
        if reversed_pair in index_map:
            original_index = index_map[reversed_pair]
            # Add the count to the original row
            df.loc[original_index, 'count'] += row['count']
            # Mark this row for deletion
            df.loc[index, 'delete'] = True
        else:
            # Store index of this pair for future reference
            index_map[(row['source_index'], row['target_index'])] = index
            # Initialize 'delete' flag to False
            df.loc[index, 'delete'] = False

    # Remove rows marked for deletion
    df = df[~df['delete']].drop(columns=['delete'])
    df.to_csv(relation_csv, index=False)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='get_entities')
    parser.add_argument('--save_entity_dir', type=str,default='./entities')
    parser.add_argument('--save_real_dir', type=str,default='./relation')
    parser.add_argument('--save_kg_dir', type=str,default='./kg')
    # 解析参数
    args = parser.parse_args()
    
    if not os.path.exists(args.save_entity_dir):
        os.makedirs(args.save_entity_dir)
    
    if not os.path.exists(args.save_real_dir):
        os.makedirs(args.save_real_dir)
    
    if not os.path.exists(args.save_kg_dir):
        os.makedirs(args.save_kg_dir)
        
    input_isolated_entities_json = os.path.join(args.save_entity_dir,'isolated_entities_merge.json')
    save_kg_nodes_json = os.path.join(args.save_kg_dir,'kg_nodes.json')
    get_kg_nodes(input_isolated_entities_json,save_kg_nodes_json)
    
    input_composed_entities_json = os.path.join(args.save_entity_dir,'composed_entities_clean.json')
    save_kg_subgraphs_json = os.path.join(args.save_kg_dir,'kg_subgraphs.json')
    get_kg_subgraphs(input_composed_entities_json,save_kg_nodes_json,save_kg_subgraphs_json)
    
    relation_csv =  os.path.join(args.save_real_dir,'all_relations.csv')
    save_kg_relation_csv = os.path.join(args.save_kg_dir,'kg_relations.csv')
    # source_node,target_node,source_entity,target_entity,type,count
    get_kg_relations(save_kg_nodes_json,save_kg_subgraphs_json,relation_csv,save_kg_relation_csv)
    keep_most_frequent_relation(save_kg_relation_csv)