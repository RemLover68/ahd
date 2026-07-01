# RAG/OCR tools reviewed for AHD

Decision: keep AHD's own backend/frontend. Do not import a full platform. Reuse Docling-style ingestion, local retrieval, and citation patterns.

## Best direct references

1. RAGFlow - full RAG/OCR/citations platform: https://github.com/infiniflow/ragflow
2. RAGFlow docs: https://ragflow.io/docs/dev/
3. PrivateGPT - private local document Q&A: https://github.com/zylon-ai/private-gpt
4. Kotaemon - document RAG app: https://github.com/Cinnamon/kotaemon
5. Open WebUI - local UI/RAG reference, not product UI: https://github.com/open-webui/open-webui
6. AnythingLLM - local workspace RAG app: https://github.com/Mintplex-Labs/anything-llm
7. Dify - LLM app platform/RAG workflows: https://github.com/langgenius/dify
8. Quivr - second-brain RAG app: https://github.com/QuivrHQ/quivr
9. Verba - Weaviate RAG app: https://github.com/weaviate/Verba
10. Onyx/Danswer - enterprise search/RAG: https://github.com/onyx-dot-app/onyx

## Parsing/OCR

11. Docling docs: https://docling-project.github.io/docling/
12. Docling GitHub: https://github.com/docling-project/docling
13. Docling paper: https://arxiv.org/abs/2501.17887
14. Unstructured: https://github.com/Unstructured-IO/unstructured
15. Marker: https://github.com/datalab-to/marker
16. Surya OCR/layout: https://github.com/datalab-to/surya
17. OCRmyPDF: https://github.com/ocrmypdf/OCRmyPDF
18. Tesseract OCR: https://github.com/tesseract-ocr/tesseract
19. PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
20. EasyOCR: https://github.com/JaidedAI/EasyOCR
21. DocTR: https://github.com/mindee/doctr
22. PyMuPDF4LLM: https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/
23. pdfplumber: https://github.com/jsvine/pdfplumber
24. pypdf: https://github.com/py-pdf/pypdf
25. Apache Tika: https://github.com/apache/tika

## RAG frameworks

26. LlamaIndex docs: https://docs.llamaindex.ai/
27. LlamaIndex CitationQueryEngine: https://developers.llamaindex.ai/python/examples/query_engine/citation_query_engine/
28. LlamaIndex Ollama integration: https://developers.llamaindex.ai/python/framework/integrations/llm/ollama/
29. LangChain: https://github.com/langchain-ai/langchain
30. Haystack: https://github.com/deepset-ai/haystack
31. txtai: https://github.com/neuml/txtai
32. LightRAG: https://github.com/HKUDS/LightRAG
33. Microsoft GraphRAG: https://github.com/microsoft/graphrag
34. Flowise: https://github.com/FlowiseAI/Flowise
35. Langflow: https://github.com/langflow-ai/langflow

## Storage/retrieval/reranking

36. Chroma: https://github.com/chroma-core/chroma
37. Qdrant: https://github.com/qdrant/qdrant
38. Milvus: https://github.com/milvus-io/milvus
39. FAISS: https://github.com/facebookresearch/faiss
40. SQLite FTS5: https://www.sqlite.org/fts5.html
41. rank-bm25: https://github.com/dorianbrown/rank_bm25
42. bm25s: https://github.com/xhluca/bm25s
43. Sentence Transformers: https://github.com/UKPLab/sentence-transformers
44. FlagEmbedding/BGE: https://github.com/FlagOpen/FlagEmbedding
45. BGE-M3 model: https://huggingface.co/BAAI/bge-m3

## Local model/runtime references

46. Ollama: https://github.com/ollama/ollama
47. Ollama API docs: https://github.com/ollama/ollama/blob/main/docs/api.md
48. Ollama OpenAI compatibility: https://github.com/ollama/ollama/blob/main/docs/openai.md
49. qwen3:14b Ollama model: https://ollama.com/library/qwen3:14b
50. Gemma 3/4 family in Ollama library: https://ollama.com/library/gemma3

## Practical result

- Use `Docling` in AHD for best local OCR/document conversion, with fallback.
- Keep current AHD FastAPI/React flow.
- Use local OpenAI-compatible endpoint against Ollama/Qwen.
- Use hybrid retrieval and forced citation markers.
- Consider Chroma/Qdrant later only if persistent corpora across jobs become necessary.
