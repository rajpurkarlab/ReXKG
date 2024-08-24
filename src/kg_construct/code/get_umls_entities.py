'''
Author: xiaoman-zhang
Date: 2024-03-17 16:10:07
LastEditors: xm_cmic
LastEditTime: 2024-05-26 21:10:07
FilePath: /2024_RadEval/src/ner/pure_ner/result_process/get_umls_entities.py
Description: 

Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
'''
import sys
import os 
import json
import pandas as pd 

from os import path
from tqdm import tqdm 
from pathlib import Path

from quickumls.constants import MEDSPACY_DEFAULT_SPAN_GROUP_NAME
import quickumls.spacy_component

import spacy
import nltk


from scispacy.abbreviation import AbbreviationDetector
from scispacy.umls_linking import UmlsEntityLinker

# source /mnt/petrelfs/share_data/zhangxiaoman/CODE/Pranav/MICIC_IV/CODE/entity_extract/.env/bin/activate 


def get_umls_entities(input_csv,save_json):
    nlp = spacy.load("en_core_sci_lg")
    abbreviation_pipe = AbbreviationDetector(nlp)
    print('Loading UmlsEntityLinker')
    linker = UmlsEntityLinker(resolve_abbreviations=True)
    print('add_pipe scispacy_linker')
    nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})
    print('process content')
    
    save_entities_dict = {} 
    df = pd.read_csv(input_csv)
    for row in tqdm(df.itertuples(), total=len(df), desc="Processing entities"):
        row_entity = row.entity
        row_entity_type = row.entity_type
        row_count = row.count 
        content_doc = nlp(row_entity)
        entities = content_doc.ents
        save_entities_dict[row_entity] = {
            'entity_type': row_entity_type,
            'count': row_count,
            'umls_info': {}
        }
        for ent in entities:
            save_entities_dict[row_entity]['umls_info'][ent.text] = []
            entity_attributes = dir(ent)
            for umls_ent in ent._.kb_ents:
                # print('umls_ent',umls_ent)
                CUI = umls_ent[0]
                possibility = umls_ent[1]
                umls_ent_info = linker.kb.cui_to_entity[CUI]
                Name = umls_ent_info[1]
                Aliases = umls_ent_info[2]
                TUI = umls_ent_info[3]
                Definition = umls_ent_info[4]
                umls_ent_dict = {
                    'CUI': CUI,
                    'Name': Name,
                    'Definition': Definition,
                    'TUI': TUI,
                    'Aliases': Aliases,
                    'Possibility': possibility
                }
                save_entities_dict[row_entity]['umls_info'][ent.text].append(umls_ent_dict)
    with open(save_json, 'w', encoding='utf-8') as output_file:
        json.dump(save_entities_dict, output_file, ensure_ascii=False, indent=4)
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='get_entities')
    parser.add_argument('--save_entity_dir', type=str,default='./entities')
    args = parser.parse_args()
    
    if not os.path.exists(args.save_entity_dir):
        os.makedirs(args.save_entity_dir)
    
        
    input_csv = os.path.join(args.save_entity_dir,'all_entities.csv')
    save_json = os.path.join(args.save_entity_dir,'all_entities_umls.json')
    get_umls_entities(input_csv,save_json)
    
    # srun -p medai --mpi=pmi2 --gres=gpu:0 -n1 --quotatype=auto --ntasks-per-node=1  --job-name=umls --kill-on-bad-exit=1 python get_umls_entities.py