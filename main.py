from pipeline.extractor import extract_text
from pipeline.parser import parse_cv
from pipeline.embedder import enrich_cv


def print_cv_report(cv: dict):
  print("\n" + "=" * 50)
  print("         CV ANALYSIS REPORT")
  print("=" * 50)

  print(f"\n📧  Email      : {cv.get('email')}")
  print(f"📞  Phone      : {cv.get('phone')}")
  print(f"📄  Text length: {cv.get('raw_text_length')} chars")

  print(f"\n🎯  Role       : {cv.get('role_category').upper()}")
  print("    Scores:")
  for role, score in sorted(cv['role_scores'].items(), key=lambda x: -x[1]):
    bar = "█" * int(score * 20)
    print(f"      {role:<12} {score:.3f}  {bar}")

  print(f"\n📊  Seniority  : {cv.get('seniority').upper()}")
  print("    Scores:")
  for level, score in sorted(cv['seniority_scores'].items(), key=lambda x: -x[1]):
    bar = "█" * int(score * 20)
    print(f"      {level:<12} {score:.3f}  {bar}")

  print(f"\n💼  Experience : {cv.get('years_experience')} year(s)  (exp score: {cv.get('total_exp_score')})")
  print("    Jobs:")
  for job in cv.get('jobs', []):
    print(f"      {job['start']} – {job['end']}  ({job['years']}y)  impact: {job['impact']}")

  print("\n" + "=" * 50 + "\n")


raw = extract_text("upload/CV_test_data_software.pdf")
parsed = parse_cv(raw)
result = enrich_cv(parsed)

print_cv_report(result)

