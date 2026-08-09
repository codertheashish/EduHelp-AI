"""
quiz.py
Generates MCQs, True/False, and Fill-in-the-blank questions from notes,
plus flashcards. Asks the AI model to return strict JSON so the frontend can
render interactive quiz/flashcard UI directly.
"""

import json
import re

from utils.openrouter_client import generate


def _extract_json(raw_text):
    """Strip markdown code fences etc. and parse JSON safely."""
    cleaned = re.sub(r"^```json|^```|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def generate_mcqs(text, count=5):
    prompt = f"""Based on the notes below, create {count} multiple-choice questions.
Return ONLY valid JSON, no other text, in this exact shape:
[
  {{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "..."}}
]

Notes:
{text[:12000]}
"""
    raw = generate(prompt)
    return _extract_json(raw)


def generate_true_false(text, count=5):
    prompt = f"""Based on the notes below, create {count} True/False questions.
Return ONLY valid JSON, no other text, in this exact shape:
[
  {{"statement": "...", "answer": true, "explanation": "..."}}
]

Notes:
{text[:12000]}
"""
    raw = generate(prompt)
    return _extract_json(raw)


def generate_fill_blanks(text, count=5):
    prompt = f"""Based on the notes below, create {count} fill-in-the-blank questions.
Use "_____" for the blank. Return ONLY valid JSON, no other text, in this exact shape:
[
  {{"question": "The capital of France is _____.", "answer": "Paris"}}
]

Notes:
{text[:12000]}
"""
    raw = generate(prompt)
    return _extract_json(raw)


def generate_flashcards(text, count=10):
    prompt = f"""Based on the notes below, create {count} flashcards (Q&A pairs)
covering the most important concepts. Return ONLY valid JSON, no other text:
[
  {{"question": "What is AI?", "answer": "Artificial Intelligence is the simulation of human intelligence by machines."}}
]

Notes:
{text[:12000]}
"""
    raw = generate(prompt)
    return _extract_json(raw)


def generate_short_answers(text, count=5):
    prompt = f"""Based on the notes below, create {count} short-answer questions
(expecting a 2-3 sentence answer). Return ONLY valid JSON:
[
  {{"question": "...", "model_answer": "..."}}
]

Notes:
{text[:12000]}
"""
    raw = generate(prompt)
    return _extract_json(raw)


def generate_long_answers(text, count=3):
    prompt = f"""Based on the notes below, create {count} long-answer / essay-style questions
(expecting a detailed multi-paragraph answer). Return ONLY valid JSON:
[
  {{"question": "...", "key_points": ["point 1", "point 2", "point 3"]}}
]

Notes:
{text[:12000]}
"""
    raw = generate(prompt)
    return _extract_json(raw)
