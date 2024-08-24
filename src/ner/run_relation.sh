srun --partition=your_partition --mpi=pmi2 --gres=gpu:1  --quotatype=auto -n1 --ntasks-per-node=1  --job-name=mimic_relation --kill-on-bad-exit=1 \
    python run_relation.py \
    --task mimic01 \
    --do_train \
    --train_file ./data/data_split/train.json \
    --model microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext \
    --do_lower_case \
    --train_batch_size 128 \
    --eval_batch_size 128 \
    --learning_rate 5e-5 \
    --num_train_epochs 20 \
    --context_window 100 \
    --max_seq_length 256 \
    --output_dir ./result/run_relation
