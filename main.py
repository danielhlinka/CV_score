# test_parser.py
from pipeline.extractor import extract_text
from pipeline.parser import parse_cv
import json

file_path = "Daniel-Hlinka-CV-EN.docx"  # swap to your actual CV path
file_path2 = "Daniel-Hlinka-CV-EN.pdf"

text = extract_text(file_path)
result = parse_cv(text)

print(json.dumps(result, indent=2, ensure_ascii=False))

text = extract_text(file_path2)
result = parse_cv(text)

print(json.dumps(result, indent=2, ensure_ascii=False))