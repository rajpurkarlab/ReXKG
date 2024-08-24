'''
Author: xm_cmic
Date: 2024-05-04 13:20:02
LastEditors: xm_cmic
LastEditTime: 2024-06-08 21:48:19
FilePath: /2024_RadEval/src_ner/chexpert/structure_data.py
Description: 

Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
'''


import os
import glob
import json 
import re
import random
import argparse
from tqdm import tqdm

def find_word_indices(sen, target_word):
    target_words = re.sub('(?<! )(?=[/,:,.,!?()])|(?<=[/,-,:,.,!?()])(?! )', r' ',target_word).split()
    start_index = -1
    end_index = -1
    for i, word in enumerate(sen):
        if word == target_words[0] and (start_index == -1 or end_index == -1):
            if sen[i:i+len(target_words)] == target_words:
                start_index = i
                end_index = i + len(target_words) - 1
    return start_index, end_index

def is_number(s):
    return s.isdigit()

def has_measurement_units(text):
    # 使用正则表达式来匹配数字后面跟着的单位，例如"8mm"、"9cm"等
    pattern = r'\d+\s*(mm|cm|m|km|in|ft|yd|mi)'
    # 在文本中搜索匹配的模式
    matches = re.findall(pattern, text)
    # 如果找到了匹配项，则返回True，否则返回False
    return bool(matches)

def get_ner_list(sen,sentence_info):
    return_ner_dict = {}
    return_ner_list = []
    for entity in list(sentence_info.keys()):
        entity_copy = entity
        if entity.lower() in ['no evidence of', 'no evidence', 'no']:
            continue
        elif 'no evidence of ' in entity.lower():
            entity = entity.replace('no evidence of ', '')
        elif 'no evidence ' in entity.lower():
            entity = entity.replace('no evidence ', '')
        elif 'no ' in entity.lower():
            entity = entity.replace('no ', '')
        entity_type = sentence_info[entity_copy].lower()
        
        if entity_type == 'size':
            if 'cm' in entity.split() or 'mm' in entity.split() or '-cm' in entity or '-mm' in entity:
                entity_type = 'size'
            elif has_measurement_units(entity) or is_number(entity):
                entity_type = 'size'
            else:
                entity_type = 'concept'
        
        if entity_type in ["devices","device"]:
            if 'removed' in sen or 'removal' in sen:
                entity_type = "devices_notpresent"
            else:
                entity_type = "devices_present"
        start_index, end_index = find_word_indices(sen, entity.lower())
        return_ner_list.append([start_index, end_index,entity_type])
        return_ner_dict[entity] = [start_index, end_index]
    return return_ner_list,return_ner_dict

def get_relation_list(sen,ner_dict,triplets_list):
    return_relation_list = []
    for triplets in triplets_list:
        source_entity = triplets['source entity'].lower()
        target_entity = triplets['target entity'].lower()
        relation = triplets['relation']
        if source_entity.lower() in ['no evidence of', 'no evidence', 'no']:
            continue
        elif 'no evidence of ' in source_entity.lower():
            source_entity = source_entity.replace('no evidence of ', '')
        elif 'no evidence ' in source_entity.lower():
            source_entity = source_entity.replace('no evidence ', '')
        elif 'no ' in source_entity.lower():
            source_entity = source_entity.replace('no ', '')
        
        if target_entity.lower() in ['no evidence of', 'no evidence', 'no']:
            continue
        elif 'no evidence of ' in target_entity.lower():
            target_entity = target_entity.replace('no evidence of ', '')
        elif 'no evidence ' in target_entity.lower():
            target_entity = target_entity.replace('no evidence ', '')
        elif 'no ' in target_entity.lower():
            target_entity = target_entity.replace('no ', '')
        
        source_start_index, source_end_index = find_word_indices(sen, source_entity.lower())
        target_start_index, target_end_index = find_word_indices(sen, target_entity.lower())
        if source_start_index == -1 or source_end_index == -1:
            try:
                source_start_index, source_end_index = ner_dict[source_entity]
            except:
                pass
        if target_start_index == -1 or target_end_index == -1:
            try:
                target_start_index, target_end_index = ner_dict[target_entity]
            except:
                pass
        return_relation_list.append([source_start_index, source_end_index,target_start_index,target_end_index,relation])
    return return_relation_list
        

def preprocess_sentences_relation(json_data,save_json_file):
    note_id_list = list(json_data.keys())
    
    final_list = []
    sentence_idx = 0
    for select_id in tqdm(note_id_list):
        data_dict_idx = json_data[select_id]
        sentence_entity_dict = data_dict_idx['res']
        sentence_relation_dict = data_dict_idx['res_relation']
        sentence_list = list(sentence_entity_dict.keys())
        relation_sentence_list = list(sentence_relation_dict.keys())
        for sentence in sentence_list:
            sen = re.sub('(?<! )(?=[/,-,:,.,!?()])|(?<=[/,-,:,.,!?()])(?! )', r' ',sentence.lower()).split()
            ner_list,ner_dict = get_ner_list(sen,sentence_entity_dict[sentence])
            try:
                temp_dict = {}
                temp_dict["doc_key"] =  str(sentence_idx)
                temp_dict["sentences"] = [sen]
                temp_dict["ner"] = [ner_list]
                try:
                    relation_list = get_relation_list(sen,ner_dict,sentence_relation_dict[sentence])
                except:
                    relation_sentence = relation_sentence_list[sentence_list.index(sentence)]
                    relation_list = get_relation_list(sen,ner_dict,sentence_relation_dict[relation_sentence])
                temp_dict["relations"] = [relation_list]
                final_list.append(temp_dict)
                sentence_idx += 1 
            except:
                print(sentence)
                pass 
            
            if(sentence_idx % 1000 == 0):
                print(f"{sentence_idx+1} sentences done")
    
    with open(save_json_file,'w') as outfile:
        for item in final_list:
            json.dump(item, outfile)
            outfile.write("\n")
    
def dict_slice(d, start, end):
    keys = list(d.keys())[start:end]
    return {k: d[k] for k in keys}

if __name__ == '__main__':
    input_json_file = './gpt4_entities_relations_chexpert_plus_post.json'
    with open(input_json_file, 'r') as json_file:
        json_data = json.load(json_file)
    
    save_train_json_file = './data_split/train.json'
    save_test_json_file = './data_split/test.json'
    
    preprocess_sentences_relation(dict_slice(json_data,0,100),save_test_json_file)
    preprocess_sentences_relation(dict_slice(json_data,100,1000),save_train_json_file)