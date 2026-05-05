from pipeline.extractor import extract_text
from pipeline.parser import parse_cv
from pipeline.embedder import enrich_cv

raw = extract_text("Daniel-Hlinka-CV-EN.docx")
parsed = parse_cv(raw)
result = enrich_cv(parsed)

for x, y in result.items():
  print(x, y)

