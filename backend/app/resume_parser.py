import io
import re

import pdfplumber


class ResumeParseError(Exception):
    pass


def extract_resume_text(content: bytes, minimum_length: int) -> str:
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [(page.extract_text() or "") for page in pdf.pages]
    except Exception as exc:
        raise ResumeParseError("Unable to read the uploaded resume.") from exc

    text = re.sub(r"[ \t]+", " ", "\n".join(pages))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(re.sub(r"\s", "", text)) < minimum_length:
        raise ResumeParseError("Your resume has no readable text. Please upload a text-based PDF.")
    return text[:50000]

