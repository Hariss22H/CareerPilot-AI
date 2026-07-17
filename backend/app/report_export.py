from io import BytesIO

from .schemas import Analysis


def build_pdf(report: dict) -> BytesIO:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=LETTER, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    story = [Paragraph("CareerPilot AI - Career Report", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph(f"Target role: {report['target_role']}", styles["Heading2"]))
    story.append(Paragraph(f"Resume: {report['resume_name']} | ATS score: {report.get('ats_score', '-')}/100", styles["Normal"]))
    analysis = Analysis.model_validate(report["analysis"])
    sections = [("ATS reasoning", [analysis.ats_reason]), ("Strengths", analysis.strengths), ("Weaknesses", analysis.weaknesses), ("Matched skills", analysis.matched_skills), ("Missing skills", analysis.missing_skills), ("Resume suggestions", analysis.resume_suggestions), ("Recruiter simulation", [analysis.rejection_reason]), ("Resume rewrite", [analysis.resume_rewrite.before, analysis.resume_rewrite.after]), ("Interview questions", analysis.interview_questions)]
    for title, items in sections:
        story.append(Spacer(1, 10)); story.append(Paragraph(title, styles["Heading2"]))
        for item in items:
            story.append(Paragraph(f"- {item}", styles["BodyText"]))
    document.build(story)
    output.seek(0)
    return output

