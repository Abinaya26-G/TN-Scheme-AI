
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

output = Path("data/pdfs/sample_scheme.pdf")
output.parent.mkdir(parents=True, exist_ok=True)

pdf = canvas.Canvas(str(output), pagesize=A4)
text = pdf.beginText(50, 790)
text.setFont("Helvetica", 11)

lines = [
    "DEMO DOCUMENT - NOT AN OFFICIAL GOVERNMENT SCHEME",
    "",
    "Sample Student Education Assistance Scheme",
    "",
    "Purpose:",
    "This fictional scheme is created only to test the RAG pipeline.",
    "",
    "Eligibility:",
    "Students enrolled in an educational institution may be considered",
    "for this fictional assistance, subject to demo rules.",
    "",
    "Documents:",
    "1. Student identity proof",
    "2. Educational institution ID",
    "3. Address proof",
    "",
    "Application process:",
    "For this demo, students submit a sample application to a fictional",
    "scheme office. This is not a real government application process.",
    "",
    "Benefits:",
    "The fictional scheme represents educational financial assistance.",
    "No actual benefit amount or eligibility is defined.",
    "",
    "IMPORTANT:",
    "This is synthetic test data, not verified official information.",
]

for line in lines:
    text.textLine(line)

pdf.drawText(text)
pdf.save()

print(f"Sample PDF created: {output}")
