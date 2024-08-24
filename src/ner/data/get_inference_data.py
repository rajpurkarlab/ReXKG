
import os
import glob
import json 
import re
import random
import argparse
from tqdm import tqdm
import pandas as pd 



def find_word_indices(sen, target_word):
    target_words = re.sub('(?<! )(?=[/,-,:,.,!?()])|(?<=[/,-,:,.,!?()])(?! )', r' ',target_word).lower().split()
    start_index = -1
    end_index = -1
    for i, word in enumerate(sen):
        if word == target_words[0] and (start_index == -1 or end_index == -1):
            if sen[i:i+len(target_words)] == target_words:
                start_index = i
                end_index = i + len(target_words) - 1
    return start_index, end_index

def get_ner_list(sen,res_dict_id):
    return_ner_list = []
    for entity, entity_type in res_dict_id.items():
        start_index, end_index = find_word_indices(sen, entity)
        return_ner_list.append([start_index, end_index,entity_type])
    return return_ner_list

def get_sentence_list(ori_report):
    # 去掉换行符
    ori_report = str(ori_report).replace('\n', '')
    # 用句号分割句子
    sentence_list = str(ori_report).split('.')
    return_sentence_list = []
    
    idx = 0
    while idx < len(sentence_list):
        sentence_idx = sentence_list[idx]
        # 检查当前句子是否以数字结尾以及下一个句子是否以数字开头
        if (idx + 1 < len(sentence_list) and 
            re.search(r'\d$', sentence_idx) and 
            re.match(r'^\d', sentence_list[idx + 1])):
            # 将当前句子与下一个句子合并
            return_sentence_list.append(sentence_idx + '.' + sentence_list[idx + 1])
            idx += 1  # 跳过下一个句子
        else:
            return_sentence_list.append(sentence_idx)
        idx += 1
    
    return return_sentence_list
            
    

def preprocess_sentences_all(input_csv_file,id_name,text_name,save_json_file):
    df = pd.read_csv(input_csv_file)
    node_id_list = df[id_name].to_list()
    report_list = df[text_name].to_list()
    
    final_list = []
    for idx in tqdm(range(len(node_id_list))):
        select_id = node_id_list[idx]
        sentence_list = get_sentence_list(report_list[idx])
        for sen_idx in range(len(sentence_list)):
            sentence = sentence_list[sen_idx]
            sen = re.sub('(?<! )(?=[/,-,:,.,!?()])|(?<=[/,-,:,.,!?()])(?! )', r' ',sentence).lower().split()
            if len(sen) < 2:
                pass 
            else:
                temp_dict = {}
                temp_dict["doc_key"] = str(select_id) + '_' + str(sen_idx)
                temp_dict["sentences"] = [sen]
                temp_dict["ner"] = [[]]
                temp_dict["relations"] = [[]]
                final_list.append(temp_dict)
        
        
    with open(save_json_file,'w') as outfile:
        for item in final_list:
            json.dump(item, outfile)
            outfile.write("\n")
            
       
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='get_entities')
    parser.add_argument('--input_csv_file', type=str,default= '../../data/chexpert_plus/df_chexpert_plus_onlyfindings.csv')
    parser.add_argument('--save_json_file', type=str,default='./chexpert_plus_groundtruth.json')
    parser.add_argument('--id_name', type=str,default='path_to_image')
    parser.add_argument('--text_name', type=str,default='section_findings')
    # 解析参数
    args = parser.parse_args()
    # path_to_image,section_findings,generated_texts
    preprocess_sentences_all(args.input_csv_file,args.id_name,args.text_name,args.save_json_file)
