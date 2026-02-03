# Research Notes: Ingestion Foundation (v0.1)

## Guiding questions (backlog)
1. What breaks first in large-scale CDC migrations (latency, schema drift, duplicates, replays)?
2. How do metadata registries scale across hundreds/thousands of datasets?
3. What are common failure modes in schema evolution under incremental loads?
4. How do regulated enterprises validate and reconcile batch vs stream?
5. What is the minimum viable lineage approach before adopting a full lineage tool?

## Initial synthesis placeholder
- This implies that contract validation and versioning should exist early, even before CDC/streaming.
