# Obligation applicability filtering (noise reduction)

What changed:
1) obligations_catalog.json: each obligation now declares `clause_types_applicable`
2) obligation_mapper.py: returns obligations with applicability metadata (optional filter support)
3) auditor.py: filters obligations per clause using `clause_types_applicable` to avoid cross-product findings
4) Added unit test: test_obligation_applicability.py

Expected impact:
- Fewer, more relevant findings
- Easier to demo (less noise)
