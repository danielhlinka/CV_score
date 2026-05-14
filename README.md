# CV Score – Dokumentace

Nástroj pro automatické hodnocení životopisu (CV) vůči pracovní pozici pomocí NLP a sémantického porovnávání.

## Použité modely
> Lokální model: `all-MiniLM-L6-v2` · AI report: `OpenAI` (default: `gpt-4o-mini`)

***

## Spuštění

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# alternativa cez Flask CLI (factory):
flask --app app:create_app run
```

Aplikace poběží na `http://localhost:5000`.  
Do `.env` přidej svoj OpenAI klíč:

```
OPENAI_API_KEY=...
# optional override:
# OPENAI_MODEL=gpt-4o-mini
```

***

## Jak funguje pipeline

```
CV (PDF/DOCX)
    │
    ▼
web/routes.py      – validácia requestu a orchestrace endpointu
web/uploads.py     – upload lifecycle (validácia, stage, cleanup)
pipeline/orchestration/scoring_pipeline.py – score orchestration service (parse → enrich → match → explain)
    │
    ▼
pipeline/input/cv_text_extractor.py – extrakcia textu z PDF/DOCX
pipeline/normalize/cv_normalizer.py – štruktúrované pole: kontakt, skills, education, experience, confidence
    │
    ▼
pipeline/enrich/profile_enricher.py – role/seniority inferencia nad normalizovanými dátami
pipeline/score/match_scorer.py      – porovná CV s požadavky pozice, vrátí skóre
    │
    ▼
pipeline/output/explanation_service.py – OpenAI model vygeneruje Markdown report
pipeline/output/sanity_logger.py       – zaloguje hodnoty a upozorní na podezřelé výsledky
```

### Váhy skóre

| Kritérium   | Váha |
|-------------|------|
| Skills      | 40% |
| Seniority   | 25% |
| Experience  | 25% |
| Role        |  5% |
| Education   |  5% |

***

## Přístup k datům

CV se zpracovává pouze po dobu požadavku: soubor je uložen dočasně pro extrakci textu a následně ihned smazán.

- **Extrakce** probíhá čistě textově (regex + řádkový parsing), bez externích modelů.
- **Embeddingy** jsou generovány lokálně pomocí `all-MiniLM-L6-v2` (sentence-transformers) – žádná data neopouštějí server, pokud nepoužiješ explainer.
- **Explainer** odesílá štruktúrované metadáta (seniority, skills, skóre) na OpenAI API – nikdy celý text CV.

***

## Struktura projektu

```
web/
├── config.py          # runtime konfigurácia (upload, debug, limity)
├── routes.py          # blueprint + / a /score
├── uploads.py         # upload validation/staging lifecycle
├── scoring_service.py # compatibility wrapper for orchestration service
├── errors.py          # centralizované HTTP/Exception handlers
└── __init__.py

pipeline/
├── constants.py       # shared domain constants and taxonomies
├── contracts.py       # typed payload contracts
├── __init__.py        # backward-compatible re-exports
├── input/
│   ├── cv_text_extractor.py
│   └── job_profile_parser.py
├── normalize/
│   ├── cv_normalizer.py
│   ├── contact_parser.py
│   ├── experience_parser.py
│   ├── skills_parser.py
│   └── education_parser.py
├── enrich/
│   ├── embedding_provider.py
│   ├── semantic_similarity.py
│   ├── seniority_model.py
│   └── profile_enricher.py
├── score/
│   ├── score_weights.py
│   ├── score_components.py
│   └── match_scorer.py
├── output/
│   ├── explanation_service.py
│   └── sanity_logger.py
├── orchestration/
│   └── scoring_pipeline.py
├── extractor.py       # compatibility wrapper
├── parser.py          # compatibility wrapper
├── normalizer.py      # compatibility wrapper
├── embedder.py        # compatibility/legacy entrypoint
├── matcher.py         # compatibility/legacy entrypoint
├── embeddings.py      # compatibility wrapper
├── semantic.py        # compatibility wrapper
├── experience.py      # compatibility wrapper
├── job_parser.py      # compatibility wrapper
├── explainer.py       # compatibility wrapper
└── sanity_check.py    # compatibility wrapper
app.py                 # Flask app factory + blueprint registration
tests/                 # regresné testy core flow + upload/service/explainer + normalizer + semantic scoring
```

## Overenie

```bash
venv/bin/python -m compileall -q app.py main.py web pipeline tests
venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```
