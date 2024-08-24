'''
Author: xm_cmic
Date: 2024-05-27 18:55:01
LastEditors: xm_cmic
LastEditTime: 2024-06-10 08:32:13
FilePath: /2024_RadEval/src/auto_kg_construct/code/structure_entities.py
Description: 

Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
'''
import os 
import json 
from tqdm import tqdm

import csv
import pandas as pd

from merge_entities import precompute_embeddings, merge_similar_entities_fast

def count_word_frequency(entities_csv_file):
    # 读取 CSV 文件
    df = pd.read_csv(entities_csv_file)
    
    # 去除 entity_type 为 size 的行
    df = df[df['entity_type'] != 'size']
    df = df[df['count'] >= 5]
    
    # 统计每个实体的单词数量
    entity_word_count = {}
    for index, row in df.iterrows():
        entity = row['entity']
        word_count = len(entity.split())
        if word_count in entity_word_count:
            entity_word_count[word_count] += 1
        else:
            entity_word_count[word_count] = 1
            
    for word_count, count in entity_word_count.items():
        print(f"单词数为 {word_count} 的实体数量: {count}")
   
def entities_by_word_count(entities_csv_file,ignore_count):
    # 读取 CSV 文件
    df = pd.read_csv(entities_csv_file)
    
    # 去除 entity_type 为 size 的行
    df = df[df['entity_type'] != 'size']
    df = df[df['count'] >= ignore_count]
    
    # 将所有的entity按单词数量存储为字典
    entity_by_word_count = {}
    for index, row in df.iterrows():
        words = remove_punctuation_and_count_words(row['entity'])
        entity = ' '.join(words)
        # entity = row['entity'].replace('- ','-').replace('/','').replace('(','').replace(')','')
        word_count = len(words)
        if word_count in entity_by_word_count:
            entity_by_word_count[word_count].append(entity)
        else:
            entity_by_word_count[word_count] = [entity]
    
    # 创建一个空字典
    entity_dict = {}
    
    # 遍历 DataFrame 的每一行，并将信息转换为字典形式
    for index, row in df.iterrows():
        words = remove_punctuation_and_count_words(row['entity'])
        entity = ' '.join(words)
        entity_type = row['entity_type']
        count = row['count']
        # entity,entity_type,count,CUI,CUI Name,Possibility
        CUI = row['CUI']
        entity_dict[entity] = {'entity_type': entity_type, 'count': count, 'CUI':CUI}
    
    return entity_by_word_count,entity_dict

def save_entities(entity_dict,isolated_entity, composed_entity, isolated_entity_csv_path, composed_entity_json_path):
    # 保存 isolated_entity 到 CSV 文件
    with open(isolated_entity_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['entity','entity_type','count','CUI'])
        for entity in isolated_entity:
            writer.writerow([entity,entity_dict[entity]['entity_type'],entity_dict[entity]['count'],entity_dict[entity]['CUI']])
    
    # 保存 composed_entity 到 JSON 文件
    with open(composed_entity_json_path, 'w', encoding='utf-8') as f:
        json.dump(composed_entity, f, ensure_ascii=False, indent=4)
        
def save_entities_withumls(entity_dict,isolated_entity,isolated_entity_dict, composed_entity, isolated_entity_csv_path, composed_entity_json_path):
    # 保存 isolated_entity 到 CSV 文件
    with open(isolated_entity_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['entity','entity_type','count','CUI'])
        for entity in isolated_entity:
            if entity in isolated_entity_dict:
                writer.writerow([entity,entity_dict[entity]['entity_type'],entity_dict[entity]['count'],isolated_entity_dict[entity]])
            else:
                writer.writerow([entity,entity_dict[entity]['entity_type'],entity_dict[entity]['count'],''])
    
    # 保存 composed_entity 到 JSON 文件
    with open(composed_entity_json_path, 'w', encoding='utf-8') as f:
        json.dump(composed_entity, f, ensure_ascii=False, indent=4)


import string
def remove_punctuation_and_count_words(text):
    # 定义标点符号表
    translator = str.maketrans('', '', string.punctuation)
    
    # 移除文本中的标点符号
    no_punctuation_text = text.translate(translator)
    
    # 分割字符串成单词列表
    words = no_punctuation_text.split()
    
    # 返回单词数量
    return words

def process_umls_singlecui_identify(file_path):
    # 读取 JSON 文件
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 初始化两个字典
    entity_cui_dict = {}
    aliases_cui_dict = {}
    all_cui_dict  = {}
    # 遍历 JSON 数据中的每一个实体
    for entity, details in data.items():
        cui = details['CUI']
        all_cui_dict[cui] = details
        aliases = details['Aliases']
        aliases = [alias.lower() for alias in aliases]
        # 填充 entity_cui_dict
        entity_cui_dict[entity.lower()] = cui
        for alias in aliases:
            entity_cui_dict[alias.lower()] = cui
        
        # 填充 aliases_cui_dict
        aliases_cui_dict[cui] = aliases
            
    return entity_cui_dict, aliases_cui_dict,all_cui_dict

def process_entities_withumls(umls_json_file,entities_csv_file,isolated_entity_csv_path, composed_entity_json_path,ignore_count): 
    # entity_dict[entity] = {'entity_type': entity_type, 'count': count, 'CUI':CUI}
    entity_cui_dict, aliases_cui_dict,_ = process_umls_singlecui_identify(umls_json_file)
    single_cui_entities = list(entity_cui_dict.keys())
    processed_entities = []
    isolated_entity = []
    isolated_entity_cui = {}
    composed_entity = {}
    entity_word_count_dict,entity_dict = entities_by_word_count(entities_csv_file,ignore_count)
    # dict_keys([1, 2, 3, 4, 5, 7, 6, 8])
    print(entity_word_count_dict.keys())
    for entity_str in entity_word_count_dict[1]:
        if entity_str in entity_cui_dict:
            cui = entity_cui_dict[entity_str]
            entity_aliases = aliases_cui_dict[cui]
            processed_entities.extend(entity_aliases)
            processed_entities = list(set(processed_entities))
            isolated_entity_cui[entity_str] = cui
            isolated_entity.append(entity_str)
            if entity_str not in entity_dict:
                entity_dict[entity_str] = {'entity_type': '', 'count': '', 'CUI':cui}
        else:
            processed_entities.append(entity_str.lower())
    isolated_entity.extend(entity_word_count_dict[1])
    print(len(isolated_entity)) # 5287
    
    if 2 in entity_word_count_dict:
        for entity in tqdm(entity_word_count_dict[2]):
            words = remove_punctuation_and_count_words(entity)
            if entity.lower() in processed_entities:
                composed_entity[entity] = words 
            elif all(word in processed_entities for word in words):
                composed_entity[entity] = words
            elif all(word in processed_entities+single_cui_entities for word in words):
                composed_entity[entity] = words
                for word in words:
                    if word in processed_entities:
                        pass 
                    else:
                        cui = entity_cui_dict[word]
                        entity_aliases = aliases_cui_dict[cui]
                        processed_entities.extend(entity_aliases)
                        processed_entities = list(set(processed_entities))
                        isolated_entity_cui[word] = cui
                        isolated_entity.append(word)
                        if word not in entity_dict:
                            entity_dict[word] = {'entity_type': '', 'count': '', 'CUI':cui}
            else:
                isolated_entity.append(entity)
                if entity_str in entity_cui_dict:
                    cui = entity_cui_dict[entity_str]
                    entity_aliases = aliases_cui_dict[cui]
                    processed_entities.extend(entity_aliases)
                    processed_entities = list(set(processed_entities))
                    isolated_entity_cui[entity_str] = cui
                    isolated_entity.append(entity_str)
                    if entity_str not in entity_dict:
                        entity_dict[entity_str] = {'entity_type': '', 'count': '', 'CUI':cui}
                else:
                    processed_entities.append(entity_str.lower())
        print(2,len(isolated_entity),len(composed_entity)) # 2 15488 21700 
        
        all_entities = entity_word_count_dict[1] + entity_word_count_dict[2]
    
    if 3 in entity_word_count_dict:
        for entity in tqdm(entity_word_count_dict[3]):
            words = remove_punctuation_and_count_words(entity)
            # words = entity.replace('- ','-').replace('/','').replace('(','').replace(')','').split()
            if entity.lower() in processed_entities:
                composed_entity[entity] = words
            elif all(word in processed_entities for word in words):
                composed_entity[entity] = words
            elif all(word in processed_entities+single_cui_entities for word in words):
                composed_entity[entity] = words
                for word in words:
                    if word in processed_entities:
                        pass 
                    else:
                        cui = entity_cui_dict[word]
                        entity_aliases = aliases_cui_dict[cui]
                        processed_entities.extend(entity_aliases)
                        processed_entities = list(set(processed_entities))
                        isolated_entity_cui[word] = cui
                        isolated_entity.append(word)
                        if word not in entity_dict:
                            entity_dict[word] = {'entity_type': '', 'count': '', 'CUI':cui}
            elif words[0] in processed_entities and ' '.join(words[1:]) in all_entities:
                composed_entity[entity] = [words[0],' '.join(words[1:])]
            elif words[:2] in all_entities and words[2] in processed_entities:
                composed_entity[entity] = [' '.join(words[:2]),words[2]]
            else:
                isolated_entity.append(entity)
                if entity_str in entity_cui_dict:
                    cui = entity_cui_dict[entity_str]
                    entity_aliases = aliases_cui_dict[cui]
                    processed_entities.extend(entity_aliases)
                    processed_entities = list(set(processed_entities))
                    isolated_entity_cui[entity_str] = cui
                    isolated_entity.append(entity_str)
                    if entity_str not in entity_dict:
                        entity_dict[entity_str] = {'entity_type': '', 'count': '', 'CUI':cui}
                else:
                    processed_entities.append(entity_str.lower())
        print(3,len(isolated_entity),len(composed_entity)) # 3 25307 54225
        all_entities = entity_word_count_dict[1] + entity_word_count_dict[2] + entity_word_count_dict[3]
    
    if 4 in entity_word_count_dict:
        for entity in tqdm(entity_word_count_dict[4]):
            words = remove_punctuation_and_count_words(entity)
            # words = entity.replace('- ','-').replace('/','').replace('(','').replace(')','').split()
            if entity.lower() in processed_entities:
                composed_entity[entity] = words
            elif all(word in isolated_entity for word in words): # 1111
                composed_entity[entity] = words
            elif words[0] in isolated_entity and ' '.join(words[1:]) in all_entities: # 13
                composed_entity[entity] = [words[0],' '.join(words[1:])]
            elif words[0] in isolated_entity and words[1] in isolated_entity and ' '.join(words[2:]) in all_entities:# 112
                composed_entity[entity] = [words[0],words[1],' '.join(words[2:])]
            elif words[0] in isolated_entity and ' '.join(words[1:3]) in all_entities and words[3] in isolated_entity:# 121
                composed_entity[entity] = [words[0],' '.join(words[1:3]),words[3]]
            elif ' '.join(words[:2]) in all_entities and words[2] in isolated_entity and words[3] in isolated_entity:# 211
                composed_entity[entity] = [' '.join(words[:2]),words[2],words[3]]
            elif ' '.join(words[:2]) in all_entities and ' '.join(words[2:]) in all_entities:# 22
                composed_entity[entity] = [' '.join(words[:2]),' '.join(words[2:])]
            else:
                isolated_entity.append(entity)
                if entity_str in entity_cui_dict:
                    cui = entity_cui_dict[entity_str]
                    entity_aliases = aliases_cui_dict[cui]
                    processed_entities.extend(entity_aliases)
                    processed_entities = list(set(processed_entities))
                    isolated_entity_cui[entity_str] = cui
                    isolated_entity.append(entity_str)
                    if entity_str not in entity_dict:
                        entity_dict[entity_str] = {'entity_type': '', 'count': '', 'CUI':cui}
                else:
                    processed_entities.append(entity_str.lower())
        print(4,len(isolated_entity),len(composed_entity)) # 4 29590 72282
    
    if 5 in entity_word_count_dict:
        for entity in tqdm(entity_word_count_dict[5]):
            words = remove_punctuation_and_count_words(entity)
            # words = entity.replace('- ','-').replace('/','').replace('(','').replace(')','').split()
            if entity.lower() in processed_entities:
                composed_entity[entity] = words
            elif all(word in isolated_entity for word in words): # 11111
                composed_entity[entity] = words
            elif words[0] in isolated_entity and ' '.join(words[1:]) in all_entities: # 14
                composed_entity[entity] = [words[0],' '.join(words[1:])]
            elif words[0] in isolated_entity and words[1] in isolated_entity and ' '.join(words[2:]) in all_entities:# 113
                composed_entity[entity] = [words[0],words[1],' '.join(words[2:])]
            elif words[0] in isolated_entity and words[4] in isolated_entity and ' '.join(words[1:4]) in all_entities:# 131
                composed_entity[entity] = [words[0],' '.join(words[1:4]),words[4]]
            elif words[0] in isolated_entity and words[1] in isolated_entity and words[2] in isolated_entity and ' '.join(words[3:]) in all_entities:# 1112            composed_entity[entity] = [words[0],words[1],' '.join(words[2:])]
                composed_entity[entity] = [words[0],words[1],words[2],' '.join(words[3:])]
            elif words[0] in isolated_entity and words[1] in isolated_entity and ' '.join(words[2:4]) in all_entities and words[4] in isolated_entity:# 1121
                composed_entity[entity] = [words[0],words[1],' '.join(words[2:4]),words[4]]
            elif words[0] in isolated_entity and ' '.join(words[1:3]) in all_entities and words[3] in isolated_entity and words[4] in isolated_entity:# 1211
                composed_entity[entity] = [words[0],' '.join(words[1:3]),words[3],words[4]]
            elif ' '.join(words[:2]) in all_entities and ' '.join(words[2:]) in all_entities:# 23
                composed_entity[entity] = [' '.join(words[:2]),' '.join(words[2:])]
            elif ' '.join(words[:2]) in all_entities and ' '.join(words[2:4]) in all_entities and words[4] in isolated_entity:# 221
                composed_entity[entity] = [' '.join(words[:2]),' '.join(words[2:4]),words[4]]
            elif ' '.join(words[:3]) in all_entities and ' '.join(words[3:]) in all_entities:# 32
                composed_entity[entity] = [' '.join(words[:3]),' '.join(words[3:])]
            elif ' '.join(words[:4]) in all_entities and words[4] in isolated_entity:# 41
                composed_entity[entity] = [' '.join(words[:4]),words[4]]
            else:
                isolated_entity.append(entity)
                if entity_str in entity_cui_dict:
                    cui = entity_cui_dict[entity_str]
                    entity_aliases = aliases_cui_dict[cui]
                    processed_entities.extend(entity_aliases)
                    processed_entities = list(set(processed_entities))
                    isolated_entity_cui[entity_str] = cui
                    isolated_entity.append(entity_str)
                    if entity_str not in entity_dict:
                        entity_dict[entity_str] = {'entity_type': '', 'count': '', 'CUI':cui}
                else:
                    processed_entities.append(entity_str.lower())
        print(5,len(isolated_entity),len(composed_entity)) # 4 30155 71498
        # save isolated_entity and composed_entity
    save_entities_withumls(entity_dict,isolated_entity, isolated_entity_cui,composed_entity, isolated_entity_csv_path, composed_entity_json_path)
 
   
def process_entities(entities_csv_file,isolated_entity_csv_path, composed_entity_json_path,ignore_count): 
    isolated_entity = []
    composed_entity = {}
    entity_word_count_dict,entity_dict = entities_by_word_count(entities_csv_file,ignore_count)
    # dict_keys([1, 2, 3, 4, 5, 7, 6, 8])
    isolated_entity.extend(entity_word_count_dict[1])
    print(len(isolated_entity)) # 5287
    for entity in tqdm(entity_word_count_dict[2]):
        words = entity.replace('- ','-').replace('/','').replace('(','').replace(')','').split()
        if all(word in isolated_entity for word in words):
            composed_entity[entity] = words
        else:
            isolated_entity.append(entity)
    print(2,len(isolated_entity),len(composed_entity)) # 2 15488 21700 
    all_entities = entity_word_count_dict[1] + entity_word_count_dict[2]
    for entity in tqdm(entity_word_count_dict[3]):
        words = entity.replace('- ','-').replace('/','').replace('(','').replace(')','').split()
        if all(word in isolated_entity for word in words):
            composed_entity[entity] = words
        elif words[0] in isolated_entity and ' '.join(words[1:]) in all_entities:
            composed_entity[entity] = [words[0],' '.join(words[1:])]
        elif words[:2] in all_entities and words[2] in isolated_entity:
            composed_entity[entity] = [' '.join(words[:2]),words[2]]
        else:
            isolated_entity.append(entity)
    print(3,len(isolated_entity),len(composed_entity)) # 3 25307 54225
    all_entities = entity_word_count_dict[1] + entity_word_count_dict[2] + entity_word_count_dict[3]
    for entity in tqdm(entity_word_count_dict[4]):
        words = entity.replace('- ','-').replace('/','').replace('(','').replace(')','').split()
        if all(word in isolated_entity for word in words): # 1111
            composed_entity[entity] = words
        elif words[0] in isolated_entity and ' '.join(words[1:]) in all_entities: # 13
            composed_entity[entity] = [words[0],' '.join(words[1:])]
        elif words[0] in isolated_entity and words[1] in isolated_entity and ' '.join(words[2:]) in all_entities:# 112
            composed_entity[entity] = [words[0],words[1],' '.join(words[2:])]
        elif words[0] in isolated_entity and ' '.join(words[1:3]) in all_entities and words[3] in isolated_entity:# 121
             composed_entity[entity] = [words[0],' '.join(words[1:3]),words[3]]
        elif ' '.join(words[:2]) in all_entities and words[2] in isolated_entity and words[3] in isolated_entity:# 211
            composed_entity[entity] = [' '.join(words[:2]),words[2],words[3]]
        elif ' '.join(words[:2]) in all_entities and ' '.join(words[2:]) in all_entities:# 22
            composed_entity[entity] = [' '.join(words[:2]),' '.join(words[2:])]
        else:
            isolated_entity.append(entity)
    print(4,len(isolated_entity),len(composed_entity)) # 4 29590 72282
    for entity in tqdm(entity_word_count_dict[5]):
        words = entity.replace('- ','-').replace('/','').replace('(','').replace(')','').split()
        if all(word in isolated_entity for word in words): # 11111
            composed_entity[entity] = words
        elif words[0] in isolated_entity and ' '.join(words[1:]) in all_entities: # 14
            composed_entity[entity] = [words[0],' '.join(words[1:])]
        elif words[0] in isolated_entity and words[1] in isolated_entity and ' '.join(words[2:]) in all_entities:# 113
            composed_entity[entity] = [words[0],words[1],' '.join(words[2:])]
        elif words[0] in isolated_entity and words[4] in isolated_entity and ' '.join(words[1:4]) in all_entities:# 131
            composed_entity[entity] = [words[0],' '.join(words[1:4]),words[4]]
        elif words[0] in isolated_entity and words[1] in isolated_entity and words[2] in isolated_entity and ' '.join(words[3:]) in all_entities:# 1112            composed_entity[entity] = [words[0],words[1],' '.join(words[2:])]
            composed_entity[entity] = [words[0],words[1],words[2],' '.join(words[3:])]
        elif words[0] in isolated_entity and words[1] in isolated_entity and ' '.join(words[2:4]) in all_entities and words[4] in isolated_entity:# 1121
             composed_entity[entity] = [words[0],words[1],' '.join(words[2:4]),words[4]]
        elif words[0] in isolated_entity and ' '.join(words[1:3]) in all_entities and words[3] in isolated_entity and words[4] in isolated_entity:# 1211
            composed_entity[entity] = [words[0],' '.join(words[1:3]),words[3],words[4]]
        elif ' '.join(words[:2]) in all_entities and ' '.join(words[2:]) in all_entities:# 23
            composed_entity[entity] = [' '.join(words[:2]),' '.join(words[2:])]
        elif ' '.join(words[:2]) in all_entities and ' '.join(words[2:4]) in all_entities and words[4] in isolated_entity:# 221
            composed_entity[entity] = [' '.join(words[:2]),' '.join(words[2:4]),words[4]]
        elif ' '.join(words[:3]) in all_entities and ' '.join(words[3:]) in all_entities:# 32
            composed_entity[entity] = [' '.join(words[:3]),' '.join(words[3:])]
        elif ' '.join(words[:4]) in all_entities and words[4] in isolated_entity:# 41
            composed_entity[entity] = [' '.join(words[:4]),words[4]]
        else:
            isolated_entity.append(entity)
    print(5,len(isolated_entity),len(composed_entity)) # 4 30155 71498
    # save isolated_entity and composed_entity
    save_entities(entity_dict,isolated_entity, composed_entity, isolated_entity_csv_path, composed_entity_json_path)
    
def clean_isolated_entities_step1(entities_csv_file,composed_entity_json_path,save_entities_csv_file):
    with open(composed_entity_json_path, 'r') as file:
        composed_entity_data = json.load(file)
    composed_entities = list(composed_entity_data.keys())
    
    df = pd.read_csv(entities_csv_file)
    # df includes entity entity_type count
    # filter df according whether 'of' or 'of the' in entity
    # for those centity contains 'A of B' or 'A of the B' 
    # Iterate over a copy of the DataFrame to avoid modification issues during iteration
    for index, row in df.copy().iterrows():
        # Check for specific patterns in the 'entity' column
        if ' of ' in row['entity']:
            
        # if row['entity'] in ['A of B', 'A of the B']:
            # Extract parts A and B
            parts = row['entity'].replace(' of the ', ' of ').split(' of ')
            A, B = parts[0], parts[1]
            
            # Check if both A and B are present as standalone entities in the DataFrame
            if (A in df['entity'].values or A in composed_entities) and (B in df['entity'].values or B in composed_entities):
                # Remove the row if both entities are found separately
                df.drop(index, inplace=True)
            else:
                pass 
                # Print A and B if one or both are not found
                # df.drop(index, inplace=True)
                # print(row['entity'],row['count'])
    
    # 分离 CUI 非空和 CUI 为空的行
    df_notna = df[pd.notna(df['CUI'])]
    df_na = df[pd.isna(df['CUI'])]

    # 只对 CUI 非空的行进行聚合
    if not df_notna.empty:  # 检查是否有非空数据
        aggregated_df = df_notna.groupby('CUI').agg({
            'entity': 'first',
            'entity_type': 'first',
            'count': 'sum'
        }).reset_index()
    else:
        aggregated_df = pd.DataFrame(columns=['CUI', 'entity', 'entity_type', 'count'])

    # 将 CUI 为空的行和聚合后的数据合并
    final_df = pd.concat([aggregated_df, df_na], ignore_index=True)
    # 根据 'count' 列排序 final_df
    final_df = final_df.sort_values(by='count', ascending=False)  # 默认为升序，设置为降序
    # 将处理后的数据保存到新的 CSV 文件
    final_df.to_csv(save_entities_csv_file, index=False)

def enhance_entity_data(json_file, csv_input_file, csv_output_file):
    # Load JSON data
    with open(json_file, 'r') as file:
        umls_data = json.load(file)
    
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_input_file)
    
    # Prepare columns for CUI, CUI Name, and Possibility
    df['CUI'] = ''
    df['CUI Name'] = ''
    df['Possibility'] = 0.0
    
    # Enhance DataFrame with UMLS information
    for index, row in tqdm(df.iterrows()):
        entity = row['entity']
        if entity in umls_data:
            # Assuming there is at least one UMLS entry per entity and we're taking the first
            try:
                entity_cui = []
                entity_cuiname = []
                entity_cuipossibility = []
                for idx in umls_data[entity]['umls_info']:
                    entity_cui.append(umls_data[entity]['umls_info'][idx][0]['CUI'])
                    entity_cuiname.append(umls_data[entity]['umls_info'][idx][0]['Name'])
                    entity_cuipossibility.append(umls_data[entity]['umls_info'][idx][0]['Possibility'])
                df.at[index, 'CUI'] = ','.join(entity_cui)
                df.at[index, 'CUI Name'] = ','.join(entity_cuiname)
                df.at[index, 'Possibility'] = ','.join(entity_cuipossibility)
                # cui_info = umls_data[entity]['umls_info'][0]
                # df.at[index, 'CUI'] = cui_info['CUI']
                # df.at[index, 'CUI Name'] = cui_info['Name']
                # df.at[index, 'Possibility'] = cui_info['Possibility']
            except:
                pass
            
    df_sorted = df.loc[df.groupby('entity')['count'].idxmax()]
    # Sort the DataFrame by 'count' in descending order
    df_sorted = df_sorted.sort_values('count', ascending=False)

    # Save the enhanced DataFrame to a new CSV file
    df_sorted.to_csv(csv_output_file, index=False)

def clean_isolated_entities_step2(input_json_file,input_csv,save_json):
    entity_cui_dict, cui_aliases_dict, all_cui_dict = process_umls_singlecui_identify(input_json_file)
    
    # 读取 CSV 文件
    df = pd.read_csv(input_csv)

    # 预处理，对于每个 CUI，合并并处理数据
    result = {}
    for _, row in df.iterrows():
        cui = row['CUI']
        entity = row['entity']
        entity_word_num = len(entity.split())
        if pd.notna(cui):
            if cui not in result:
                # 初始化字典结构
                alias_list = [row['entity']]
                alias_list.extend(cui_aliases_dict[cui])
                alias_list = list(set(alias_list))
                result[cui] = all_cui_dict[cui]
                result[cui]['Aliases'] = alias_list
                result[cui]['entity_type'] = row['entity_type']
                result[cui]['count'] = row['count']
            else:
                # 累加 count 和更新别名列表
                result[cui]['count'] += row['count']
                if row['entity'] not in result[cui]['Aliases']:
                    result[cui]['Alias'].append(row['entity'])
        else:
            if 'no' in row['entity'].split():
                pass 
            else:
                result[row['entity']] = {
                        'entity_type': row['entity_type'],
                        'count': row['count'],
                        'CUI': row['entity'],
                        'Name': '',
                        'Possibility': 0.0,
                        'Aliases': [row['entity']]
                    }

    # 结果是按 CUI 组织的，如果需要按 entity 组织的结果
    # final_result = {v['Aliases'][0]: v for v in result.values()}

    # 输出到 JSON 文件
    with open(save_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4) 


def clean_composed_entities(isolated_entities_json_file,composed_entity_json_path,save_composed_entity_json_path):
    # 读取 JSON 文件
    with open(isolated_entities_json_file, 'r', encoding='utf-8') as file:
        isolated_entities_data = json.load(file)
    
    # 初始化两个字典
    entity_cui_dict = {}
    # 遍历 JSON 数据中的每一个实体
    for entity, details in isolated_entities_data.items():
        cui = details['CUI']
        if cui == '':
            cui = entity.lower()
        aliases = details['Aliases']
        aliases = [alias.lower() for alias in aliases]
        for alias in aliases:
            if alias.lower() in entity_cui_dict:
                if cui[0] == 'C':
                    entity_cui_dict[alias.lower()] = cui
                else:
                    pass 
            else:
                entity_cui_dict[alias.lower()] = cui
        
    with open(composed_entity_json_path, 'r', encoding='utf-8') as file:
        composed_entities_data = json.load(file)
    save_composed_entities_data_dict = {}
    for composed_entity in composed_entities_data:
        entity_list = composed_entities_data[composed_entity]
        composed_entity_cui_list = []
        for entity in entity_list:
            if entity in entity_cui_dict:
                composed_entity_cui_list.append(entity_cui_dict[entity])
            elif entity in  save_composed_entities_data_dict:
                composed_entity_cui_list.extend(save_composed_entities_data_dict[entity]['cui_list'])
            else:
                entity_list = entity.replace(' of the ',' ').replace(' of ',' ').split()
                for entity in entity_list:
                    if entity in entity_cui_dict:
                        composed_entity_cui_list.append(entity_cui_dict[entity])
                    elif entity in  save_composed_entities_data_dict:
                        composed_entity_cui_list.extend(save_composed_entities_data_dict[entity]['cui_list'])
                    else:
                        pass
        save_composed_entities_data_dict[composed_entity] = {
            "composed_cui": '/'.join(sorted(composed_entity_cui_list)),
            "cui_list": composed_entity_cui_list,
            "entity_list": entity_list
        }
        
    # 初始化新的数据结构
    transformed_data = {}

    # 遍历原始数据并构建新的结构
    for entity_name, details in save_composed_entities_data_dict.items():
        composed_cui = details['composed_cui']
        cui_list = details['cui_list']
        entity_list = details['entity_list']

        # 检查是否已经有该 composed_cui 的条目
        if composed_cui in transformed_data:
            # 如果存在，添加到 composed_entities 列表
            transformed_data[composed_cui]['composed_entities'].append(entity_name)
        else:
            # 如果不存在，创建新的条目
            transformed_data[composed_cui] = {
                'composed_entities': [entity_name],
                'cui_list': cui_list,
                'entity_list': entity_list
            }
            
    with open(save_composed_entity_json_path, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, ensure_ascii=False, indent=4) 

        
        
        
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='get_entities')
    parser.add_argument('--save_entity_dir', type=str,default='./entities')
    parser.add_argument('--language_model', type=str,default='ncbi/MedCPT-Query-Encoder') # FremyCompany/BioLORD-2023-C
    parser.add_argument('--threshold', type=float,default=0.95)
    parser.add_argument('--ignore_count', type=int,default=5)
    # 解析参数
    args = parser.parse_args()
    
    if not os.path.exists(args.save_entity_dir):
        os.makedirs(args.save_entity_dir)
    
        
    entities_csv_file = os.path.join(args.save_entity_dir,'all_entities.csv')
    umls_singlecui_json_file = os.path.join(args.save_entity_dir,'all_entities_umls_singlecui.json')
    umls_singlecui_identify_json_file = os.path.join(args.save_entity_dir,'all_entities_umls_singlecui_identify.json')
    # get all cui of all entities
    enhance_entity_data(umls_singlecui_json_file, entities_csv_file, entities_csv_file)
    # count_word_frequency(entities_csv_file)
    
    # get isolated entities and composed entities
    isolated_entity_csv_path = os.path.join(args.save_entity_dir,'isolated_entities.csv')
    composed_entity_json_path = os.path.join(args.save_entity_dir,'composed_entities.json')
    process_entities_withumls(umls_singlecui_identify_json_file,entities_csv_file,isolated_entity_csv_path, composed_entity_json_path,args.ignore_count)
    # merge isolated entities using MedCPT/BioLORD for example calcification and calcifications
    # 1. for those contains 'A of B' or 'A of the B' check if A and B in isolated entities, if so, remove from isolated_entities, else print 
    save_entities_csv_file = os.path.join(args.save_entity_dir,'isolated_entities_clean.csv')
    clean_isolated_entities_step1(isolated_entity_csv_path,composed_entity_json_path,save_entities_csv_file)
    
    save_entities_json_file = os.path.join(args.save_entity_dir,'isolated_entities_clean.json')
    clean_isolated_entities_step2(umls_singlecui_identify_json_file,save_entities_csv_file,save_entities_json_file)
    
    save_merge_isolated_entity_json_file = os.path.join(args.save_entity_dir,'isolated_entities_merge.json')
    embeddings_dict_file = os.path.join(args.save_entity_dir,'isolated_entities_clean_embeddings.pth')
    precompute_embeddings(save_entities_json_file,embeddings_dict_file,args.language_model)
    merge_similar_entities_fast(save_entities_json_file,save_merge_isolated_entity_json_file,embeddings_dict_file,threshold=args.threshold)
    
    """
    "C5237503": {
        "CUI": "C5237503",
        "Name": "Periventricular",
        "Definition": "Of, or pertaining to, the area surrounding the ventricles of the brain.",
        "TUI": [
            "T082"
        ],
        "Aliases": [
            "periventricular"
        ],
        "Possibility": 1.0
    },
    """
    
    # 得到所有的composed_entities 
    save_composed_entity_json_path = os.path.join(args.save_entity_dir,'composed_entities_clean.json')
    clean_composed_entities(save_merge_isolated_entity_json_file,composed_entity_json_path,save_composed_entity_json_path)
    
    """
    "C0016169/paranasal": {
        "composed_entities": ["paranasal sinuses"],
        "cui_list": [
            "paranasal",
            "C0016169"
        ],
        "entity_list": [
            "paranasal",
            "sinuses"
        ]
    }
    """