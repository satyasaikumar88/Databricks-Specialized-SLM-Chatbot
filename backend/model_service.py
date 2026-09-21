from __future__ import annotations

import json
import os
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from backend.config import settings


class LocalModelService:
    def __init__(self):
        self.model_name = settings.model_name
        self.base_model_path = Path(settings.base_model_path)
        self.fine_tuned_model_path = Path(settings.fine_tuned_model_path)
        self.device = 'cuda' if settings.use_gpu and torch.cuda.is_available() else 'cpu'
        self.tokenizer = None
        self.model = None
        try:
            self.load()
        except Exception as exc:
            print(f'Warning: model initialization failed: {exc}')

    def load(self):
        model_id = self.model_name
        if self.base_model_path.exists():
            model_id = str(self.base_model_path)

        if self.fine_tuned_model_path.exists():
            adapter_path = self.fine_tuned_model_path
            self.tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True, cache_dir=settings.hf_home)
            base_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                low_cpu_mem_usage=True,
                cache_dir=settings.hf_home,
            )
            self.model = PeftModel.from_pretrained(base_model, str(adapter_path))
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, cache_dir=settings.hf_home)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                low_cpu_mem_usage=True,
                cache_dir=settings.hf_home,
            )

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.to(self.device)
        self.model.eval()

    def generate(self, prompt: str, max_new_tokens: int = 220, temperature: float = 0.7) -> str:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError('Model is not initialized.')

        encoded = self.tokenizer(prompt, return_tensors='pt').to(self.device)
        with torch.no_grad():
            output = self.model.generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=(temperature > 0),
                pad_token_id=self.tokenizer.eos_token_id,
            )
        text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return text.replace(prompt, '').strip()

    def get_model_info(self) -> dict:
        return {
            'model_name': self.model_name,
            'device': self.device,
            'adapter_exists': self.fine_tuned_model_path.exists(),
            'base_model_path': str(self.base_model_path),
            'fine_tuned_model_path': str(self.fine_tuned_model_path),
        }


model_service = LocalModelService()
