
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
            'context': "<Input> Unchanged position of the left upper extremity PICC line. Again seen are surgical clips projecting over the right hemithorax.   Increased stranding opacities are noted in the left retrocardiac region.<\Input>",
            'response': "{'Unchanged position of the left upper extremity PICC line.':{'Unchanged': 'concept','position':'concept','left' : 'concept', 'upper': 'concept','extremity':'anatomy','PICC line':'device_present'}, 'Again seen are surgical clips projecting over the right hemithorax. ':{'surgical clips':'device_present', 'right' : 'concept',  'hemithorax': 'anatomy'},'Increased stranding opacities are noted in the left retrocardiac region. ':{'Increased':'concept','stranding' : 'concept','opacities': 'disorder_present','left':'concept','retrocardiac':'anatomy','region':'anatomy'}}"
        }
    ]
    
    messages = [ 
            {"role": "system", "content": "You are a radiologist performing clinical term extraction from the FINDINGS and IMPRESSION sections in the radiology report. \
                    Here a clinical term can be in ['anatomy','disorder_present','disorder_notpresent','procedures','devices','concept', 'devices_present','devices_notpresent','size']. \
                    'anatomy' refers to the anatomical body;\
                    'disorder_present' refers to findings or diseases are present according to the sentence; \
                    'disorder_notpresent' refers to findings or diseases are not present according to the sentence; \
                    'procedures' refers to procedures are used to diagnose, measure, monitor or treat problems; \
                    'devices' refers to any instrument, apparatus for medical purpose. \
                    'size' refers to the measurement of disorders or anatomy, for example, '3mm','4x5 cm'. \
                    'concept' refers to descriptors such as 'acute' or 'chronic','large', size or severity, or other modifiers, or descriptors of anatomy being normal. \
                    For example, right pleural effusion , 'right' should be a 'concept', and 'pleural' should be  'anatomy' and 'effusion' should be 'disorder-present' or 'disorder-notpresent'.\
                    For example, normal cardiomediastinal silhouette. 'normal' and 'silhouette' should be 'concept', 'cardiomediastinal' should be 'anatomy'.  \
                    Please extract terms one word at a time whenever possible, avoiding phrases. Note that terms like 'no' and 'no evidence of' are not considered entities. \
                    Given a list of radiology sentence input in the format: \
                    <Input><sentence><sentence><\Input> \
                    Please reply with the JSON format following template: {'<sentence>':{'entity':'entity type','entity':'entity type'},'<sentence>':{'entity':'entity type','entity':'entity type'}} \
                   "
                }
            ]
    
    for sample in fewshot_samples:
        messages.append({"role":"user", "content":sample['context']})
        messages.append({"role":"assistant", "content":sample['response']})
    messages.append({"role":"user", "content":query})
    return messages

        
def chatgpt_input(messages):
    response = openai.ChatCompletion.create(
        # model="gpt-3.5-turbo",
        # model = "gpt-4-1106-preview",
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


     
def estimate_cost(prompt_tokens, completion_tokens):
    input_cost = 0.005
    output_cost = 0.015
    return (input_cost*prompt_tokens/1000 + output_cost*completion_tokens/1000)

def test_prompt(findings_idx):
    content =  '<Input>' + findings_idx + '<\Input>'
    messages = get_messages(content)
    res,cost = chatgpt_input(messages)
    return res,cost
            
def evaluate_notes(input_csv_file,save_json_file,start_idx,end_idx): 
    #    ,path_to_image,path_to_dcm,frontal_lateral,ap_pa,deid_patient_id,patient_report_date_order,report,section_narrative,section_clinical_history,section_history,section_comparison,section_technique,section_procedure_comments,section_findings,section_impression,section_end_of_impression,section_summary,section_accession_number,age,sex,race,ethnicity,interpreter_needed,insurance_type,recent_bmi,deceased,split
    df = pd.read_csv(input_csv_file)[0:1000]
    image_id_list = df['path_to_image'].to_list()
    findings_list = df['section_findings'].to_list()
    
    # # Process and save selected data to a newJSON file
    summary_cost = 0
    try:
        with open(save_json_file, 'r') as outfile:
            save_data_dict = json.load(outfile)
    except:
        save_data_dict = {}
            
    for idx in tqdm(range(start_idx,end_idx)):
        image_idx = image_id_list[idx]
        findings_idx = findings_list[idx]
        if image_idx in save_data_dict:
            print('Already passed:',image_idx)
        else:
            save_data_dict_idx = {}
            save_data_dict_idx['section_findings'] = findings_idx
            try:
                res,cost = test_prompt(findings_idx)
                summary_cost += cost
                save_data_dict_idx['res'] = res
                save_data_dict_idx['cost'] = cost
                save_data_dict[image_idx] = save_data_dict_idx
            except:
                print(idx,image_idx)
                time.sleep(1)
            with open(save_json_file, 'w') as outfile:
                json.dump(save_data_dict, outfile, indent=4) 
    print('SUMMARY COST: ',summary_cost)
            

if __name__ == '__main__':
    openai.api_key = "api-key"
    openai.api_base = "api-base"

    input_csv_file = '../../data/chexpert_plus/df_chexpert_plus_200401_withfindings.csv'
    save_json_file ='./gpt4_entities_chexpert_plus.json'
    
    evaluate_notes(input_csv_file,save_json_file,start_idx=0,end_idx=1000)
