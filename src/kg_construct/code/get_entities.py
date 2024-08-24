import os
import json
import csv
import re
from operator import itemgetter
from collections import OrderedDict, defaultdict, Counter
from tqdm import tqdm

def is_number(s):
    return s.isdigit()

def has_measurement_units(text):
    # Use regex to match numbers followed by units, e.g., "8mm", "9cm", etc.
    pattern = r'\d+\s*(mm|cm|m|km|in|ft|yd|mi)'
    # Search for matching patterns in the text
    matches = re.findall(pattern, text)
    # Return True if matches are found, otherwise False
    return bool(matches)

def contains_digit(s):
    return any(char.isdigit() for char in s)

def extract_entities(json_file):
    # Extract all entities
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Save all entities
    all_entities = defaultdict(lambda: defaultdict(int))
    # Save by count 
    entities_count = {}
    
    for entry in data:
        entities = entry.get('entities', {})
        for entity, category in entities.items():
            entity = entity.lower()
            if 'cm' in entity.split() or 'mm' in entity.split() or '-cm' in entity or '-mm' in entity:
                category = 'size'
            elif has_measurement_units(entity) or is_number(entity):
                category = 'size'
            else:
                category = category.split('_')[0]
            
            if contains_digit(entity) and category != 'size':
                continue
            
            all_entities[entity][category] += 1
            if category not in entities_count:
                entities_count[category] = {}
            if entity not in entities_count[category]:
                entities_count[category][entity] = 0
            entities_count[category][entity] += 1
    
    # Sort all_entities by count value from high to low
    sorted_entities = sorted(all_entities.items(), key=lambda x: sum(x[1].values()), reverse=True)

    with open(os.path.join(args.save_entity_dir, 'all_entities.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['entity', 'entity_type', 'count'])
        for entity, types_count in sorted_entities:
            sorted_types_count = sorted(types_count.items(), key=itemgetter(1), reverse=True)
            for entity_type, count in sorted_types_count:
                writer.writerow([entity, entity_type, count])

def filter_max_count(csv_file):
    entity_max_count = {}
    # Read CSV file and record the row with the maximum count for each entity
    with open(csv_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            entity = row['entity']
            count = int(row['count'])
            if entity not in entity_max_count or count > entity_max_count[entity]['count']:
                entity_max_count[entity] = {'entity_type': row['entity_type'], 'count': count}

    # Write filtered rows to a new CSV file
    with open(os.path.join(args.save_entity_dir, 'all_entities.csv'), 'w', newline='') as csvfile:
        fieldnames = ['entity', 'entity_type', 'count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entity, data in entity_max_count.items():
            writer.writerow({'entity': entity, 'entity_type': data['entity_type'], 'count': data['count']})

    # Create a separate CSV file for each entity_type
    for entity_type in set(row['entity_type'] for row in entity_max_count.values()):
        csv_file = os.path.join(args.save_entity_dir, f'{entity_type}.csv')
        with open(csv_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['entity', 'count'])
            for entity, data in entity_max_count.items():
                if data['entity_type'] == entity_type:
                    writer.writerow([entity, data['count']])

def extract_relations(input_json_file, save_csv_file):
    with open(input_json_file, 'r') as file:
        input_data = json.load(file)
    
    relation_rows = []
    for data_idx in tqdm(input_data):
        relations = data_idx.get('relations', {})
        for relation_idx in relations:
            relation_rows.append([relation_idx["source_entity"].lower(), relation_idx["target_entity"].lower(), relation_idx["type"]])
    
    # Use Counter to count the occurrences of each row
    count_dict = Counter(tuple(row) for row in relation_rows)

    # Sort and write results to CSV file
    with open(save_csv_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['source_entity', 'target_entity', 'type', 'count'])
        for key, value in sorted(count_dict.items(), key=lambda x: x[1], reverse=True):
            csvwriter.writerow([key[0], key[1], key[2], value])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Entity and Relation Extraction')
    parser.add_argument('--ent_pred_mimic_headct', type=str, default=None)
    parser.add_argument('--ent_real_pred_mimic_headct', type=str, default=None)
    parser.add_argument('--save_entity_dir', type=str, default='./entities')
    parser.add_argument('--save_real_dir', type=str, default='./relation')
    args = parser.parse_args()
    
    if not os.path.exists(args.save_entity_dir):
        os.makedirs(args.save_entity_dir)
    
    if not os.path.exists(args.save_real_dir):
        os.makedirs(args.save_real_dir)
        
    # Extract all entities and their corresponding entity types
    extract_entities(args.ent_pred_mimic_headct)
    # For each entity, save the most frequently predicted category as its entity_type, save a file for each entity_type
    filter_max_count(os.path.join(args.save_entity_dir, 'all_entities.csv'))
    # Extract all relations
    extract_relations(args.ent_real_pred_mimic_headct, os.path.join(args.save_real_dir, 'all_relations.csv'))