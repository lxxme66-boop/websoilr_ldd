# Fix for BM25Retriever Import Error

## Problem
The error `ModuleNotFoundError: No module named 'llama_index.core.retrievers.bm25'` occurs because BM25Retriever has been moved to a separate package in newer versions of llama-index.

## Solution

### 1. Install the Required Package
```bash
pip install llama-index-retrievers-bm25
```

If you encounter an "externally-managed-environment" error, use:
```bash
pip install --break-system-packages llama-index-retrievers-bm25
```

### 2. Update the Import Statement
In your `retrieve_nodes.py` file (or `/mnt/workspace/LLM/ldd/raft-master/utils/retrieve_nodes.py`), change:

```python
# OLD (incorrect)
from llama_index.core.retrievers.bm25 import BM25Retriever
```

To:

```python
# NEW (correct)
from llama_index.retrievers.bm25 import BM25Retriever
```

### 3. No Other Changes Required
The rest of your code can remain the same. The BM25Retriever API is unchanged, only the import path has changed.

## Additional Notes
- The package `llama-index-retrievers-bm25` is now a separate module from `llama-index-core`
- This change was made to modularize the llama-index library
- The functionality of BM25Retriever remains the same

## Verification
After making these changes, your script should run without the import error.