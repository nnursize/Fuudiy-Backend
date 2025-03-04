# server/routes/translation.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import torch
import asyncio
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import subprocess
import os

router = APIRouter()

HF_ACCESS_TOKEN = os.getenv("HF_ACCESS_TOKEN")


command = f"huggingface-cli login --token {HF_ACCESS_TOKEN}"

# Run the command in the shell
subprocess.run(command, shell=True, check=True)

# Load translation models
models = {
    "tr-en": {
        "tokenizer": AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-tr-en"),
        "model": AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-tr-en"),
    },
    "en-tr": {
        "tokenizer": AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-trk"),
        "model": AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-trk"),
    },
}

# Ensure models run on GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
for key in models:
    models[key]["model"].to(device)

# Request model
class TranslationRequest(BaseModel):
    text: str
    target_lang: str  # "en" for English, "tr" for Turkish

@router.post("/", tags=["Translation"])
async def translate(request: TranslationRequest):
    text = request.text.strip()
    text = text.encode("utf-8").decode("utf-8")  # Ensure UTF-8 encoding
    target_lang = request.target_lang.lower()

    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    
    if target_lang not in ["en", "tr"]:
        raise HTTPException(status_code=400, detail="Invalid target language. Use 'en' or 'tr'.")

    # Select the correct model and tokenizer
    lang_pair = "tr-en" if target_lang == "en" else "en-tr"
    tokenizer = models[lang_pair]["tokenizer"]
    model = models[lang_pair]["model"]

    try:
        translated_text = await asyncio.to_thread(run_translation, text, tokenizer, model)
        return {"translated_text": translated_text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

def run_translation(text: str, tokenizer, model) -> str:
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(device)
    with torch.no_grad():
        translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)
