# CV Score – Dokumentace

Nástroj pro automatické hodnocení životopisu (CV) vůči pracovní pozici pomocí NLP a sémantického porovnávání.

## Použité modely
> Lokální model: `all-MiniLM-L6-v2` · AI report: `Claude Sonnet` (default: `claude-sonnet-4-6`)

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
Do `.env` přidej svoj Anthropic klíč:

```
ANTHROPIC_API_KEY=...
# optional override:
# ANTHROPIC_MODEL=claude-sonnet-4-6
```

## CI / test gate

```bash
python -m compileall -q app.py main.py pipeline
python -m unittest discover -s tests -p "test*.py" -v
```

***

## Jak funguje pipeline

```
CV (PDF/text)
    │
    ▼
extractor.py       – extrahuje sekce: skills, education, work, other
    │
    ▼
embedder.py        – vytvoří embedding celého CV (vážené sekce)
experience.py      – parsuje pracovní zkušenosti, délku a seniority
    │
    ▼
matcher.py         – porovná CV s požadavky pozice, vrátí skóre
    │
    ▼
explainer.py       – Claude Sonnet vygeneruje Markdown report
sanity_check.py    – zaloguje hodnoty a upozorní na podezřelé výsledky
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
- **Explainer** odesílá štruktúrované metadáta (seniority, skills, skóre) na Anthropic API – nikdy celý text CV.

***

## Struktura projektu

```
pipeline/
├── extractor.py       # sekce z textu CV
├── embedder.py        # embedding + seniority
├── embeddings.py      # get_embedding, classify_role
├── experience.py      # pracovní historie, délka, level
├── matcher.py         # výsledné skóre
├── job_parser.py      # parsování formuláře s pozicí
├── explainer.py       # LLM report
├── sanity_check.py    # debug logging
└── __init__.py
app.py                 # Flask server
```
