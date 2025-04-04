# Datafiler

Denna katalog innehåller datafiler som används av boten.

## Genererade filer
Följande filer genereras automatiskt och ingår inte i Git-repositoriet på grund av filstorlek:

- `knowledge_index.faiss` - Kunskapsindexet för FAISS
- `knowledge_texts.npy` - Textrepresentationer för kunskapsbasen

För att generera dessa filer, kör följande kommandon från projektets rot:

```bash
python utils/extract_all_pdfs.py
python utils/index_knowledge.py
```

## Övriga datafiler
- `user_colors.json` - Användarnas färginställningar
- `rules/` - Textuella regelrefererenser
- `rolls.db` - SQLite-databas med historik över tärningskast
