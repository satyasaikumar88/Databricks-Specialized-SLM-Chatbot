from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling


SYSTEM_PROMPT = "You are a Databricks expert. Answer using Databricks best practices, lakehouse architecture, and Spark/Delta/Unity Catalog knowledge. Be concise, factual, and grounded in official Databricks concepts."


def format_instruction(example: dict) -> str:
    question = example.get('question', '').strip()
    answer = example.get('answer', '').strip()
    return f"<s>[INST] {SYSTEM_PROMPT}\n\nQuestion: {question} [/INST]\nAnswer: {answer}</s>\n"


def load_jsonl(path: str | Path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def train_model(
    model_name: str,
    dataset_path: str,
    output_dir: str,
    epochs: int = 1,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    max_samples: int = 500,
    max_length: int = 512,
):
    os.makedirs(output_dir, exist_ok=True)
    dataset_rows = load_jsonl(dataset_path)[:max_samples]
    dataset = load_dataset('json', data_files=dataset_path, split='train').select(range(min(len(dataset_rows), max_samples)))

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    def preprocess(examples):
        texts = [format_instruction({'question': q, 'answer': a}) for q, a in zip(examples['question'], examples['answer'])]
        return tokenizer(texts, truncation=True, padding='max_length', max_length=max_length)

    tokenized = dataset.map(preprocess, batched=True, batch_size=8)
    tokenized = tokenized.remove_columns(dataset.column_names)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map='auto' if torch.cuda.is_available() else None,
    )

    config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
        lora_dropout=0.05,
        bias='none',
        task_type='CAUSAL_LM',
    )
    model = get_peft_model(model, config)
    model.print_trainable_parameters()

    training_kwargs = dict(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        save_strategy='epoch',
        logging_steps=10,
        num_train_epochs=epochs,
        fp16=torch.cuda.is_available(),
        bf16=torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8,
        remove_unused_columns=False,
        report_to=[],
        dataloader_num_workers=0,
    )
    try:
        training_kwargs['eval_strategy'] = 'no'
        args = TrainingArguments(**training_kwargs)
    except TypeError:
        training_kwargs['evaluate_strategy'] = 'no'
        args = TrainingArguments(**training_kwargs)

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f'Model saved to {output_dir}')


def main():
    parser = argparse.ArgumentParser(description='Fine-tune an SLM with LoRA on a Databricks instruction dataset.')
    parser.add_argument('--model_name', type=str, default='Qwen/Qwen2.5-0.5B-Instruct')
    parser.add_argument('--dataset_path', type=str, default='data/databricks_qa.jsonl')
    parser.add_argument('--output_dir', type=str, default='model/qwen2.5-0.5B-databricks-lora')
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--batch_size', type=int, default=2)
    parser.add_argument('--learning_rate', type=float, default=2e-4)
    parser.add_argument('--max_samples', type=int, default=200)
    parser.add_argument('--max_length', type=int, default=512)
    args = parser.parse_args()

    train_model(
        model_name=args.model_name,
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_samples=args.max_samples,
        max_length=args.max_length,
    )


if __name__ == '__main__':
    main()
