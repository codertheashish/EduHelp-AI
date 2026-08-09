"""
summary.py
Generates summaries of uploaded notes at different lengths/styles,
and exports a summary to a downloadable PDF.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from utils.openrouter_client import generate

SUMMARY_DIR = "summaries"
os.makedirs(SUMMARY_DIR, exist_ok=True)


def summarize(text, style="300_words"):
    """style: '100_words' | '300_words' | 'bullet_points'"""
    instructions = {
        "100_words": "Summarize the following notes in about 100 words.",
        "300_words": "Summarize the following notes in about 300 words.",
        "bullet_points": "Summarize the following notes as a concise list of bullet points, "
                          "covering every key concept.",
    }
    instruction = instructions.get(style, instructions["300_words"])

    prompt = f"""{instruction}

Notes:
{text[:12000]}
"""
    return generate(prompt)


def export_summary_pdf(summary_text, title, doc_id):
    """Render a summary as a PDF file and return its filepath."""
    filepath = os.path.join(SUMMARY_DIR, f"{doc_id}_summary.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                             leftMargin=2 * cm, rightMargin=2 * cm,
                             topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    for para in summary_text.split("\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), styles["BodyText"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return filepath
