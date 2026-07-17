import io
import re

import pdfplumber


class JobDescriptionError(Exception):
    pass


def extract_job_description(content: bytes, filename: str, content_type: str, minimum_length: int = 40) -> str:
    is_pdf = content_type == "application/pdf" or filename.lower().endswith(".pdf")
    is_txt = content_type.startswith("text/") or filename.lower().endswith((".txt", ".text"))
    if not (is_pdf or is_txt):
        raise JobDescriptionError("Job descriptions must be PDF or TXT files.")
    try:
        if is_pdf:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                raw = "\n".join(page.extract_text() or "" for page in pdf.pages)
        else:
            raw = content.decode("utf-8-sig")
    except Exception as exc:
        raise JobDescriptionError("Unable to read the uploaded job description.") from exc
    text = re.sub(r"[ \t]+", " ", raw)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(re.sub(r"\s", "", text)) < minimum_length:
        raise JobDescriptionError("The job description does not contain enough readable text.")
    return text[:50000]
