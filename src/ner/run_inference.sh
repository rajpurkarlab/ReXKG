srun --partition=your_partition --mpi=pmi2 --gres=gpu:1  --quotatype=auto -n1 --ntasks-per-node=1  --job-name=mimic --kill-on-bad-exit=1 \
    python run_entity.py \
    --do_eval \
    --eval_test \
    --learning_rate=1e-5 \
    --task_learning_rate=5e-4 \
    --train_batch_size=8 \
    --eval_batch_size 2048 \
    --context_window 100\
    --task mimic01 \
    --data_dir ./data \
    --test_data your_test_file.json \
    --test_pred_filename ent_pre_your_test_file.json \
    --model microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext \
    --output_dir ./result/run_entity


srun --partition=your_partition --mpi=pmi2 --gres=gpu:1  --quotatype=auto -n1 --ntasks-per-node=1  --job-name=mimic_relation --kill-on-bad-exit=1 \
    python run_relation.py \
    --task mimic01 \
    --do_eval \
    --eval_test \
    --model microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext \
    --do_lower_case \
    --train_batch_size 16 \
    --eval_batch_size 2048 \
    --learning_rate 2e-5 \
    --num_train_epochs 10 \
    --context_window 100 \
    --max_seq_length 256 \
    --entity_output_dir ./result/run_entity \
    --entity_predictions_test ent_pre_your_test_file.json \
    --output_dir ./result/run_relation \
    --prediction_file ent_real_pre_your_test_file.json
