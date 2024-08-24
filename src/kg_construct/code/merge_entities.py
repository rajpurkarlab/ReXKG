'''
Author: xm_cmic
Date: 2024-06-02 10:21:55
LastEditors: xm_cmic
LastEditTime: 2024-06-02 13:51:57
FilePath: /2024_RadEval/src/ner/pure_ner/result_process/merge_entities.py
Description: 

Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
'''
import os

from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from tqdm import tqdm 
import json
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def get_medcpt_embedding(tokenizer,model,alias):
    with torch.no_grad():
        encoded = tokenizer(
            alias, 
            truncation=True, 
            padding=True, 
            return_tensors='pt', 
            max_length=64,
        )
        
        # encode the queries (use the [CLS] last hidden states as the representations)
        embeds = model(**encoded).last_hidden_state[:, 0, :].detach()
    return embeds

def get_biolord_embedding(tokenizer,model,alias):
    # Tokenize sentences
    encoded_input = tokenizer(alias, padding=True, truncation=True, return_tensors='pt')
    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
    # print(sentence_embeddings.shape) torch.Size([1, 768])
    return sentence_embeddings

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def precompute_embeddings(input_json_file,save_file,language_model):
    json_data = load_json(input_json_file)
    tokenizer = AutoTokenizer.from_pretrained(language_model)
    model = AutoModel.from_pretrained(language_model)
    embeddings_dict = {}
    for key, entry in tqdm(json_data.items()):
        alias_embeddings = []
        for alias in entry['Aliases']:
            # Compute embedding only once per alias
            if alias not in embeddings_dict:
                if language_model == 'FremyCompany/BioLORD-2023-C':
                    embeddings_alias = get_biolord_embedding(tokenizer,model,[alias])
                elif language_model == 'ncbi/MedCPT-Query-Encoder':
                    embeddings_alias = get_medcpt_embedding(tokenizer,model,[alias])
            alias_embeddings.append(embeddings_alias)
        # Store the mean of embeddings for the entry
        if alias_embeddings:
            embeddings_dict[key] = torch.mean(torch.stack(alias_embeddings), dim=0)
    # Save embeddings to file
    print(len(embeddings_dict))
    torch.save(embeddings_dict, save_file)
    print(f"Embeddings saved to {save_file}")

def merge_similar_entities_fast(input_json_file,save_json_file, embeddings_dict_file,threshold):
    json_data = load_json(input_json_file)
    
    # Load the embeddings dictionary from the file
    embeddings_dict = torch.load(embeddings_dict_file)
    all_similar_entries = []
    # Prepare data for efficient cosine similarity computation
    labels = list(embeddings_dict.keys())
    embeddings = torch.stack(list(embeddings_dict.values())).numpy()  # Convert to numpy array for sklearn
    # Compute the cosine similarity matrix
    similarity_matrix = cosine_similarity(embeddings[:,0,:])
    
    # Find similar entries based on the similarity threshold
    results = {}
    for idx, row in enumerate(similarity_matrix):
        similar_entries = []
        for jdx, similarity in enumerate(row):
            if idx != jdx and similarity >= threshold:  # Avoid comparing to itself and check threshold
                if labels[jdx] in results:
                    pass 
                else:
                    similar_entries.append(labels[jdx])
                    all_similar_entries.append(labels[jdx])
        
        if similar_entries:
            results[labels[idx]] = similar_entries
            print(labels[idx], similar_entries)
    
    save_json_data = json_data.copy()
    for key, entry in tqdm(json_data.items()):
        if key in results:
            similar_entries = results[key]
            for similar_entry in similar_entries:
                similar_entry_dict = json_data[similar_entry]
                save_json_data[key]['Aliases'].extend(similar_entry_dict['Aliases'])
                save_json_data[key]['count'] += similar_entry_dict['count']
        elif key in all_similar_entries:
            del save_json_data[key]
    
    # Save results to a JSON file
    with open(save_json_file, 'w', encoding='utf-8') as f:
        json.dump(save_json_data, f, indent=4)
    print(f"Results saved to {save_json_file}")
    


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='get_entities')
    parser.add_argument('--save_entity_dir', type=str,default='./auto_build_kg_full/entities')
    parser.add_argument('--language_model', type=str,default='ncbi/MedCPT-Query-Encoder') # FremyCompany/BioLORD-2023-C
    parser.add_argument('--threshold', type=float,default=0.95)
    
    args = parser.parse_args()
    isolated_entity_json_file = os.path.join(args.save_entity_dir,'isolated_entities_clean.json')
    save_merge_isolated_entity_json_file = os.path.join(args.save_entity_dir,'isolated_entities_merge_biolord.json')
    embeddings_dict_file = os.path.join(args.save_entity_dir,'isolated_entities_clean_embeddings_biolord.pth')
    precompute_embeddings(isolated_entity_json_file,embeddings_dict_file,args.language_model)
    merge_similar_entities_fast(isolated_entity_json_file,save_merge_isolated_entity_json_file,embeddings_dict_file,threshold=args.threshold)