"""
Author: xm_cmic
Date: 2024-05-04 15:21:50
LastEditors: xm_cmic
LastEditTime: 2024-05-26 21:23:16
FilePath: /2024_RadEval/src/ner/pure_ner/result_process/filter_cui.py
Description: Filter and process UMLS CUI data
Copyright (c) 2024 by ${git_name_email}, All Rights Reserved.
"""

import os
import json
from tqdm import tqdm
import string

def remove_punctuation_and_count_words(text):
    # Define punctuation table
    translator = str.maketrans('', '', string.punctuation)
    
    # Remove punctuation from the text
    no_punctuation_text = text.translate(translator)
    
    # Split string into word list
    words = no_punctuation_text.split()
    
    # Return word count and word list
    return len(words), words

def filter_umls_cui(input_json_file, save_json_file, save_identify_json_file):
    with open(input_json_file, 'r') as file:
        all_entity_data = json.load(file)
    
    all_entities = list(all_entity_data.keys())
    print('All entities:', len(all_entities))
    
    save_entity_dict = {}
    save_identify_entity_dict = {}
    
    for entity in all_entities:
        entity_info = all_entity_data[entity]
        entity_umls_info = entity_info['umls_info']
        
        if 'cm' in entity.split() or 'mm' in entity.split():
            pass
        elif len(entity_umls_info) == 0:
            save_entity_dict[entity] = entity_info
        else:
            save_entity_dict[entity] = entity_info
            for entity_text in entity_umls_info:
                if len(entity_umls_info[entity_text]) == 0:
                    save_entity_dict[entity]['umls_info'][entity_text] = []
                else:
                    entity_flag = 0
                    for entity_umls_info_idx in entity_umls_info[entity_text]:
                        name = entity_umls_info_idx['Name'].lower()
                        alias_list = [alias.lower() for alias in entity_umls_info_idx['Aliases']]
                        
                        if entity.lower() == name:
                            save_entity_dict[entity]['umls_info'][entity_text] = [entity_umls_info_idx]
                            save_identify_entity_dict[entity] = entity_umls_info_idx
                            entity_flag = 1
                            break
                        elif entity.lower() in alias_list:
                            save_entity_dict[entity]['umls_info'][entity_text] = [entity_umls_info_idx]
                            save_identify_entity_dict[entity] = entity_umls_info_idx
                            entity_flag = 1
                            break
                    
                    if entity_flag == 0:
                        save_entity_dict[entity]['umls_info'][entity_text] = [entity_umls_info[entity_text][0]]
    
    with open(save_json_file, 'w', encoding='utf-8') as output_file:
        json.dump(save_entity_dict, output_file, indent=4)
    
    with open(save_identify_json_file, 'w', encoding='utf-8') as output_file:
        json.dump(save_identify_entity_dict, output_file, indent=4)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Filter UMLS CUI')
    parser.add_argument('--save_entity_dir', type=str, default='./entities')
    args = parser.parse_args()
    
    if not os.path.exists(args.save_entity_dir):
        os.makedirs(args.save_entity_dir)
    
    input_json_file = os.path.join(args.save_entity_dir, 'all_entities_umls.json')
    save_json_file = os.path.join(args.save_entity_dir, 'all_entities_umls_singlecui.json')
    save_identify_json_file = os.path.join(args.save_entity_dir, 'all_entities_umls_singlecui_identify.json')
    
    filter_umls_cui(input_json_file, save_json_file, save_identify_json_file)