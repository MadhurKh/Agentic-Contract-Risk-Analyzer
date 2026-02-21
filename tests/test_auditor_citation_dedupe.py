from types import SimpleNamespace

from src.agents.auditor import run_auditor
from src.rag.store import RagIndex, RagChunk
import numpy as np


def test_auditor_dedupes_citations():
    # Build a tiny fake index with duplicate chunks
    chunks = [
        RagChunk(doc_id="EU-AIA", chunk_id="c1", text="logging traceability requirements", meta={"page": 10, "jurisdiction": "EU", "title": "EU AI Act"}),
        RagChunk(doc_id="EU-AIA", chunk_id="c1", text="logging traceability requirements", meta={"page": 10, "jurisdiction": "EU", "title": "EU AI Act"}),
        RagChunk(doc_id="EU-AIA", chunk_id="c2", text="human oversight requirements", meta={"page": 20, "jurisdiction": "EU", "title": "EU AI Act"}),
    ]
    vocab = {"logging":0,"traceability":1,"human":2,"oversight":3,"requirements":4}
    idf = np.ones((len(vocab),), dtype=np.float32)
    tfidf = np.ones((len(chunks), len(vocab)), dtype=np.float32)
    index = RagIndex(vocabulary=vocab, idf=idf, tfidf_matrix=tfidf, chunks=chunks)

    clauses = [{"clause_id":"C1","clause_type":"LOGGING","clause_text":"We will maintain audit logging.","evidence_spans":[{"clause_ref":"C1","snippet":"audit logging"}]}]
    obligations = [{"obligation_id":"EU-AIA-LOGGING-01","jurisdiction":"EU","title":"Logging","requirement":"Keep logs","applies_if":"","clause_types_applicable":["LOGGING"],"severity_default":"MEDIUM","tags":["logging","traceability"]}]

    findings = run_auditor(clauses=clauses, obligations=obligations, rag_index=index).data["findings"]
    assert len(findings) == 1
    cits = findings[0]["reg_citations"]
    # duplicates should be removed
    keys = {(c["doc_id"], c["page"], c["chunk_id"]) for c in cits}
    assert len(keys) == len(cits)
