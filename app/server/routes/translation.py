# server/routes/translation.py
"""
from fastapi import APIRouter
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

router = APIRouter()

tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-tr-en")
model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-tr-en")

@router.post("/translate/")
async def translate(text: str):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    translated = model.generate(**inputs)
    translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    return {"translated_text": translated_text}
"""