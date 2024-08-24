srun --partition=your_partition --mpi=pmi2 --gres=gpu:1  --quotatype=auto -n1 --ntasks-per-node=1  --job-name=mimic --kill-on-bad-exit=1 \
    python run_entity.py \
    --do_train \
    --do_eval \
    --eval_test \
    --learning_rate=1e-5 \
    --task_learning_rate=5e-4 \
    --train_batch_size=8 \
    --context_window 100\
    --task mimic01 \
    --data_dir ./data \
    --train_data ./data/data_split/train.json \
    --dev_data  ./data/data_split/test.json \
    --test_data  ./data/data_split/test.json \
    --model microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext \
    --output_dir ./result/run_entity

