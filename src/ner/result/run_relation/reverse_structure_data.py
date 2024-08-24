import os
import glob
import json 
import re
import random
import argparse
from tqdm import tqdm

def preprocess_sentences(input_json_file,save_json_file):
    with open(input_json_file, 'r', encoding='utf-8') as file:
        # 读取 JSON 文件
        data = [json.loads(line) for line in file]

    processed_data = []
    for doc in tqdm(data):
        # 合并句子
        sentences = ' '.join(doc['sentences'][0])
        
        predicted_entities = {}
        for entity_info in doc['predicted_ner'][0]:
            start, end, entity_type = entity_info
            entity_text = ' '.join(doc['sentences'][0][start:end + 1])
            predicted_entities[entity_text] = entity_type
        
        predicted_relations = []
        for relation_info in doc['predicted_relations'][0]:
            if relation_info:  # 确保关系信息不为空
                start1, end1, start2, end2, relation_type = relation_info
                entity1_text = ' '.join(doc['sentences'][0][start1:end1 + 1])
                entity2_text = ' '.join(doc['sentences'][0][start2:end2 + 1])
                predicted_relations.append({'source_entity': entity1_text, 'target_entity': entity2_text, 'type': relation_type})


        processed_doc = {
            'doc_key': doc['doc_key'],
            'sentences': sentences,
            'entities': predicted_entities,
            'relations': predicted_relations
        }

        processed_data.append(processed_doc)
    
    with open(save_json_file, 'w', encoding='utf-8') as output_file:
        json.dump(processed_data, output_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    input_json_file = './ent_pre_your_test_file.json'
    save_json_file = '../../data/your_test_file.json'
    preprocess_sentences(input_json_file,save_json_file)