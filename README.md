# CV Score – Dokumentace

Nástroj pro automatické hodnocení životopisu (CV) vůči pracovní pozici pomocí NLP a sémantického porovnávání.

## Použité modely
> Lokální model: `all-MiniLM-L6-v2` · AI report: `GPT-4o-mini`

***

## Spuštění

```bash
pip install -r requirements.txt
python app.py
```

Aplikace poběží na `http://localhost:5000`.  
Do `.env` přidej svůj OpenAI klíč:

```
OPENAI_API_KEY=sk-...
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
explainer.py       – GPT-4o-mini vygeneruje Markdown report
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

CV není ukládáno – zpracovává se výhradně v paměti za běhu požadavku.

- **Extrakce** probíhá čistě textově (regex + řádkový parsing), bez externích modelů.
- **Embeddingy** jsou generovány lokálně pomocí `all-MiniLM-L6-v2` (sentence-transformers) – žádná data neopouštějí server, pokud nepoužiješ explainer.
- **Explainer** odesílá strukturovaná metadata (seniority, skills, skóre) na OpenAI API – nikdy celý text CV.

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
├── explainer.py       # GPT report
├── sanity_check.py    # debug logging
└── __init__.py
app.py                 # Flask server
```