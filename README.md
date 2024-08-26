# ReXKG

ReXKG is a system that extracts structured information from processed reports to construct a comprehensive radiology knowledge graph.

## Project Structure

```
src/
├── data/
│   └── chexpert_plus/
│   ├── ──df_chexpert_plus_onlyfindings.csv
├── ner/
│   ├── data/
│   ├── entity/
│   ├── relation/
│   ├── shared/
│   ├── run_entity.py
│   └── run_relation.py
└── kg_construct/
    └── code/
    └── result/
```


## System Overview

The ReXKG system consists of three main components:

1. Information Extraction System
2. Node Construction
3. Edge Construction

## Information Extraction System

We use the entity extraction method proposed by [PURE](https://github.com/princeton-nlp/PURE.git) for our information extraction system.

### Installation and Dependencies
`conda env create -f environment.yml`

### Training

1. **Data Preparation**:
   Annotate data with GPT4, split it into train and test
   `./src/ner/data`
   Run `python gpt4_entity_extraction.py` and `python gpt4_relation_extraction.py`
   Run `python structure_data.py` to convert report data into the format used by PURE for training. 

2. **Entity Extraction**:
   `./src/ner`
   Run `sh run_entity.sh` to train the entity extraction model.

3. **Relation Extraction**:
   `./src/ner`
   Run `sh run_relation.sh` to train the relation extraction model.

4. **Inference**:
   `./src/ner/data`
   You can also download model checkpoint from [Google Drive](https://drive.google.com/drive/folders/1DZY7L0JUQcV2mwThOeT8tYmLvVFDy3PN?usp=sharing) to ./result/
   Convert data file in to the test format with `python get_inference_data.py`
   `./src/ner`
   Run `sh inference.sh` to perform inference on the entire dataset.

5. **Data Post-processing**:
   Run `python ./result/run_relation/reverse_structure_data.py` to prepare the data for node construction and edge construction.

## Node Construction and Edge Construction

### Installation and Dependencies

`./src/kg_construct/code`

1. run `sh auto_build_kg.sh` to get kg at `result`


## Citation
If you use this code for your research or project, please cite:

    @article{zhang2024uncovering,
      title={Uncovering Knowledge Gaps in Radiology Report Generation Models through Knowledge Graphs},
      author={Zhang, Xiaoman and Zhou, Hong-Yu and N. Acosta, Juli´an and Rajpurkar, Pranav},
      journal={arXiv},
      year={2024},
    }

If you have any question, please feel free to contact.

