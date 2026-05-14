Manual facts in this directory are loaded at runtime and injected directly into prompt context.

Rules:
- Use one `.json` file per fact or a JSON array of facts in a single file.
- Manual facts are never embedded.
- Manual facts are never written into Chroma/vector DB.
- Retrieval order is `manual_facts -> vector_retrieval -> rerank -> prompt assembly`.

Example:

```json
{
  "fact_id": "ayaka_family_0",
  "character": "Kamisato Ayaka",
  "category": "family",
  "priority": 10,
  "aliases": [
    "gia dinh",
    "family",
    "anh trai",
    "brother"
  ],
  "text": "Kamisato Ayaka is the younger sister of Kamisato Ayato."
}
```
