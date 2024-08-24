
import openai
import json
import re
import csv
import time
import random
import pandas as pd
from tqdm import tqdm

def get_messages(query):
    fewshot_samples = [
        {
            'context': "{'Bones are stable with mild degenerative changes of the spine.':{'Bones': 'anatomy', 'stable': 'concept', 'mild': 'concept', 'degenerative changes': 'disorder_present', 'spine': 'anatomy'}}",
            'response': "{'Bones are stable with mild degenerative changes of the spine.': [{'stable': 'Bones', 'relation':'modify'}, {'mild':'degenerative changes', 'relation':'modify'}, {'degenerative changes':'spine','relation':'located_at'}]}"
        },
        {
            'context': "{'A dense retrocardiac opacity remains present with slight blunting of the left costophrenic angle, suggestive of a small effusion.': {'dense': 'concept','retrocardiac': 'anatomy','opacity': 'disorder_present','slight': 'concept','blunting': 'disorder_present','left': 'concept','costophrenic': 'anatomy','angle': 'anatomy','small': 'concept','effusion': 'disorder_present'}}",
            'response': "{'A dense retrocardiac opacity remains present with slight blunting of the left costophrenic angle, suggestive of a small effusion.': [{'dense': 'opacity', 'relation': 'modify'}, {'opacity': 'retrocardiac', 'relation': 'located_at'}, {'slight': 'blunting', 'relation': 'modify'}, {'blunting': 'angle', 'relation': 'modify'}, {'left': 'costophrenic', 'relation': 'modify'}, {'small': 'effusion', 'relation': 'modify'}, {'effusion': 'costophrenic', 'relation': 'located_at'},{'opacity':'effusion','relation':'suggestive_of'},{'blunting':'effusion','relation':'suggestive_of'}]}"
        }
    ]
    
    messages = [ 
            {"role": "system", "content": "You are a radiologist performing relation extraction of entities from the FINDINGS and IMPRESSION sections in the radiology report. \
                    Here a clinical term can be in ['anatomy','disorder_present','disorder_notpresent','procedures','devices','concept', 'devices_present','devices_notpresent', 'size']. \
                    And the relation can be in ['modify', 'located_at', 'suggestive_of']. \
                    'suggestive_of' means the source entity (findings) may suggest the target entity (disease). \
                    'located_at' means the source entity is located at the target entity. \
                    'modify' denotes the source entity modifies the target entity. \
                    Every time there is a 'modify' relationship between concept and anatomy, the direction should be concept -> anatomy. \
                    For example, right pleural effusion , 'right' (concept), modify  'pleural' (anatomy), 'effusion' (disorder) located_at 'pleural' (anatomy). \
                    Please ensure the direction of source/target entities is maintained correctly. \
                    Given a piece of radiology text input in the JSON format: \
                    {'sentence':{'entity':'entity_type'},'sentence':{'entity':'entity_type'}} \
                    Please reply with the following JSON format: \
                    {'sentence':[{source entity:'target entity',relation:'relation'},{source entity:'target entity',relation:'relation'}]} \
                   "
                }
            ]
    
    for sample in fewshot_samples:
        messages.append({"role":"user", "content":sample['context']})
        messages.append({"role":"assistant", "content":sample['response']})
    messages.append({"role":"user", "content":query})
    return messages

def estimate_cost(prompt_tokens, completion_tokens):
    input_cost = 0.005
    output_cost = 0.015
    return (input_cost*prompt_tokens/1000 + output_cost*completion_tokens/1000)


def chatgpt_input(messages):
    response = openai.ChatCompletion.create(
        # model="gpt-3.5-turbo",
        model = "gpt-4o-2024-05-13",
        messages= messages,
        response_format={"type": "json_object"}
    )
    try:
        res = response["choices"][0]["message"]["content"]
        cost = estimate_cost(response["usage"]["prompt_tokens"],response["usage"]["completion_tokens"])
        return json.loads(res),cost
    except:
        res = response["choices"][0]["message"]["content"]
        cost = estimate_cost(response["usage"]["prompt_tokens"],response["usage"]["completion_tokens"])
        return res,cost

def test_prompt(input_json):
    messages = get_messages(input_json)
    res,cost = chatgpt_input(messages)
    return res,cost

def evaluate_notes(json_file,save_json_file):  
    
    with open(json_file, 'r') as file:
        json_data = json.load(file)
    note_id_list = list(json_data.keys())
    summary_cost = 0
    
    try:
        with open(save_json_file, 'r') as file:
            save_data_dict = json.load(file)
    except:
        save_data_dict = {}
    
    for select_id in tqdm(note_id_list):
        if select_id in save_data_dict:
            pass 
        else:
            data_dict_idx = json_data[select_id]
            save_data_dict_idx = data_dict_idx.copy()
            input_json = data_dict_idx['res']
            
            res,cost = test_prompt(json.dumps(input_json))
            summary_cost += cost
            save_data_dict_idx['res_relation'] = res
            save_data_dict_idx['cost'] = cost
            save_data_dict[select_id] = save_data_dict_idx
            
        with open(save_json_file, 'w') as outfile:
            json.dump(save_data_dict, outfile, indent=4) 
    print('SUMMARY COST: ',summary_cost)

def convert_json_format(input_dict):
    if len(input_dict) == 2:
        source_entity, target_entity = input_dict.items()
        return {
            "source entity": source_entity[0],
            "target entity": input_dict[source_entity[0]],
            "relation": input_dict[target_entity[0]]
        }
    elif len(input_dict) == 3:
        if "source" in input_dict:
            input_dict["source entity"] = input_dict["source"]
            input_dict["target entity"] = input_dict["target"]
            del input_dict["source"]
            del input_dict["target"]
        return input_dict
    else:
        print('Error:',input_dict)
        return None

def flatten_dict(d):
    flat_dict = {}
    
    for key, value in d.items():
        if isinstance(value, dict):
            # 如果值是一个字典，递归展开并合并到当前字典
            flat_dict.update(flatten_dict(value))
        else:
            flat_dict[key] = value
            
    return flat_dict

def postprocess_json(input_json_file,save_json_file):
    with open(input_json_file, 'r') as file:
        json_data = json.load(file)
    note_id_list = list(json_data.keys())
    
    save_data_dict = {}
    for select_id in tqdm(note_id_list):
        data_dict_idx = json_data[select_id]
        save_data_dict_idx = data_dict_idx.copy()
        res_dict_idx = data_dict_idx['res']
        res_relation_dict_idx = data_dict_idx['res_relation']
        save_res_relation_dict_idx = res_relation_dict_idx.copy()
        sentence_list = list(res_dict_idx.keys())
        relation_sentence_list = list(res_relation_dict_idx.keys())
        if len(sentence_list) != len(relation_sentence_list):
            pass 
        else:
            for sentence in res_dict_idx:
                res_dict_idx[sentence] = flatten_dict(res_dict_idx[sentence])
            for sentence in res_relation_dict_idx:
                sentence_relation_list = res_relation_dict_idx[sentence]
                # print(sentence,sentence_relation_list)
                save_sentence_relation_list = []
                for sentence_relation_dict in sentence_relation_list:
                    save_sentence_relation_dict = convert_json_format(sentence_relation_dict)
                    if save_sentence_relation_dict:
                        save_sentence_relation_list.append(save_sentence_relation_dict)
                save_res_relation_dict_idx[sentence] = save_sentence_relation_list
            save_data_dict_idx['res_relation'] = save_res_relation_dict_idx
            save_data_dict[select_id] = save_data_dict_idx
    
    with open(save_json_file, 'w') as outfile:
            json.dump(save_data_dict, outfile, indent=4) 
        

if __name__ == '__main__':
    openai.api_key = "api-key"
    openai.api_base = "api-base"

    input_json_file ='./gpt4_entities_chexpert_plus.json'
    save_json_file ='./gpt4_entities_relations_chexpert_plus.json'
    evaluate_notes(input_json_file,save_json_file)
    postprocess_json_file = './gpt4_entities_relations_chexpert_plus_post.json'
    postprocess_json(save_json_file,postprocess_json_file)
    