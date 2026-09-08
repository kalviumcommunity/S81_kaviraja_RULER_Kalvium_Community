# Source Citation & Attribution Demo

## Verified cited answer

**Question:** What is RAG?

**Answer:** RAG retrieves facts from an external knowledge base to ground language models in accurate, up-to-date information. **[1]**

| Citation | Source | Location |
| --- | --- | --- |
| [1] | `doc2.txt` (`DOC2`) | `What is RAG?`, page 1, `DOC2#chunk_001`, characters 0-599 |

**Original retrieved text used for generation:**

> Retrieval-Augmented Generation (RAG) is an AI framework for retrieving facts from an external knowledge base to ground large language models (LLMs) on the most accurate, up-to-date information and to give users insight into LLMs' generative process.

**Verification:** `VERIFIED_AGAINST_RETRIEVED_CHUNK`

## No-source fallback

When retrieval returns no supporting chunks, or the model omits a valid marker, the system returns:

> The provided context does not contain sufficient information to answer this question with a verifiable citation.

It returns `citations: []` and does not invent a filename, chunk ID, or page.
