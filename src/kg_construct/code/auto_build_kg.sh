srun -p your_partition  --job-name=step1 --kill-on-bad-exit=1 python get_entities.py --ent_pred_mimic_headct ../data/chexpert_plus/chexpert_plus_groundtruth.json --ent_real_pred_mimic_headct ../data/chexpert_plus/chexpert_plus_groundtruth.json --save_entity_dir ../result/chexpert_plus/chexpert_plus_groundtruth/entities --save_real_dir ../result/chexpert_plus/chexpert_plus_groundtruth/relation

srun -p your_partition  --job-name=step2 --kill-on-bad-exit=1 python get_umls_entities.py --save_entity_dir ../result/chexpert_plus/chexpert_plus_groundtruth/entities 

srun -p your_partition  --job-name=step3 --kill-on-bad-exit=1 python filter_cui.py --save_entity_dir ../result/chexpert_plus/chexpert_plus_groundtruth/entities 

srun -p your_partition  --job-name=step4 --kill-on-bad-exit=1 python structure_entities.py --save_entity_dir ../result/chexpert_plus/chexpert_plus_groundtruth/entities  --ignore_count 10

srun -p your_partition  --job-name=step5 --kill-on-bad-exit=1 python get_kg_nodes.py --save_entity_dir ../result/chexpert_plus/chexpert_plus_groundtruth/entities  --save_real_dir ../result/chexpert_plus/chexpert_plus_groundtruth/relation  --save_kg_dir ../result/chexpert_plus/chexpert_plus_groundtruth/kg 

srun -p your_partition  --job-name=step6 --kill-on-bad-exit=1 python get_size_relations.py --entity_dir ../result/chexpert_plus/chexpert_plus_groundtruth/entities  --real_dir ../result/chexpert_plus/chexpert_plus_groundtruth/relation 

