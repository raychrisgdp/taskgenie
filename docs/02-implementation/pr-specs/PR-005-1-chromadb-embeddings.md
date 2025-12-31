# PR-005-1: ChromaDB Setup & Embeddings Pipeline (Spec)

**Status:** Spec Only
**Depends on:** PR-001, PR-004
**Last Reviewed:** 2025-12-31

## Goal

Implement ChromaDB vector store, embedding service with sentence-transformers, and automatic task/attachment indexing pipeline.

## User Value

- Tasks and cached attachment content are automatically searchable
- Semantic search will work (foundation for PR-005-2)
- Embeddings are generated and stored efficiently

## Scope

### In

- `RAGService` class in `backend/services/rag_service.py`
- `EmbeddingService` class in `backend/services/embedding_service.py`
- ChromaDB persistent client setup
- sentence-transformers model: `all-MiniLM-L6-v2`
- Task indexing: on create/update via database hooks
- Attachment indexing: on content fetch
- Batch indexing support
- Collection management (get/create/reset)

### Out

- Semantic search endpoint (PR-005-2)
- RAG context injection (PR-005-2)
- Chat integration with RAG (PR-005-2)
- Remote vector DB support

## Mini-Specs

- Persistent ChromaDB client at `settings.vector_store_path`
- Embedding generation via sentence-transformers (`all-MiniLM-L6-v2`)
- Index tasks on create/update and attachments on content fetch
- Batch indexing support for rebuilds/imports

## References

- `docs/01-design/DESIGN_DATA.md` (document structure + metadata)
- `docs/01-design/DESIGN_CHAT.md` (RAG strategy)
- `docs/01-design/API_REFERENCE.md` (search endpoint examples; implemented in PR-005-2)

## Technical Design

### Embedding Service

```python
# backend/services/embedding_service.py
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    """Service for generating text embeddings."""

    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load embedding model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def generate(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]

    def similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Calculate cosine similarity between embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        dot = np.dot(vec1, vec2)
        norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return float(dot / norm)


# Singleton instance
embedding_service = EmbeddingService()
```

### RAG Service - Setup & Indexing

```python
# backend/services/rag_service.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from typing import Optional
from backend.config import settings
from backend.services.embedding_service import embedding_service

class RAGService:
    """Service for RAG operations with ChromaDB."""

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: str = "tasks",
    ):
        self.persist_directory = persist_directory or settings.vector_store_path
        self.collection_name = collection_name
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None

    @property
    def client(self) -> chromadb.ClientAPI:
        """Lazy-initialize ChromaDB client."""
        if self._client is None:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create tasks collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 100,
                    "hnsw:search_ef": 50,
                },
            )
        return self._collection

    def build_document(self, task: dict) -> str:
        """Build searchable document from task data."""
        parts = [
            task.get("title", ""),
            task.get("description", ""),
        ]

        # Include attachment content
        for attachment in task.get("attachments", []):
            if isinstance(attachment, dict):
                parts.append(attachment.get("title", ""))
                parts.append(attachment.get("content", ""))
            elif isinstance(attachment, str):
                parts.append(attachment)

        # Include tags
        tags = task.get("tags", [])
        if tags:
            parts.append(" ".join(tags))

        return " ".join(filter(None, parts))

    async def index_task(self, task: dict) -> str:
        """Index a task in ChromaDB."""
        task_id = task["id"]
        document = self.build_document(task)
        embedding = embedding_service.generate(document)

        self.collection.upsert(
            ids=[task_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[{
                "task_id": task_id,
                "status": task.get("status", "pending"),
                "priority": task.get("priority", "medium"),
                "has_attachments": len(task.get("attachments", [])) > 0,
            }],
        )
        return task_id

    async def index_tasks_batch(self, tasks: list[dict]) -> list[str]:
        """Index multiple tasks in a batch."""
        if not tasks:
            return []

        ids = [t["id"] for t in tasks]
        documents = [self.build_document(t) for t in tasks]
        embeddings = embedding_service.generate_batch(documents)
        metadatas = [
            {
                "task_id": t["id"],
                "status": t.get("status", "pending"),
                "priority": t.get("priority", "medium"),
                "has_attachments": len(t.get("attachments", [])) > 0,
            }
            for t in tasks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return ids

    async def delete_task(self, task_id: str) -> bool:
        """Remove task from index."""
        try:
            self.collection.delete(ids=[task_id])
            return True
        except Exception:
            return False

    def reset(self):
        """Reset collection (for testing/migration)."""
        self.client.delete_collection(self.collection_name)
        self._collection = None


# Singleton instance
rag_service = RAGService()
```

### Configuration

**Environment Variables**
```bash
# .env
TASKGENIE_DATA_DIR=~/.taskgenie
```

**Config File**
```toml
# ~/.taskgenie/config.toml
[app]
data_dir = "~/.taskgenie"

[rag]
collection_name = "tasks"
embedding_model = "all-MiniLM-L6-v2"
```

### Database Hooks

**On Task Create/Update**
```python
# backend/api/tasks.py (or database triggers)
from backend.services.rag_service import rag_service

@router.post("", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession):
    # Save to database
    db_task = Task(**task.dict())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    # Index in ChromaDB
    task_dict = task_to_dict(db_task)
    await rag_service.index_task(task_dict)

    return TaskResponse.from_orm(db_task)

@router.patch("/{id}", response_model=TaskResponse)
async def update_task(id: str, task: TaskUpdate, db: AsyncSession):
    # Update in database
    db_task = await get_task_or_404(id, db)
    for field, value in task.dict(exclude_unset=True).items():
        setattr(db_task, field, value)
    await db.commit()

    # Re-index in ChromaDB
    task_dict = task_to_dict(db_task)
    await rag_service.index_task(task_dict)

    return TaskResponse.from_orm(db_task)

@router.delete("/{id}", status_code=204)
async def delete_task(id: str, db: AsyncSession):
    db_task = await get_task_or_404(id, db)
    await db.delete(db_task)
    await db.commit()

    # Remove from ChromaDB
    await rag_service.delete_task(id)
```

**On Attachment Fetch**
```python
# backend/api/attachments.py
from backend.services.rag_service import rag_service

@router.post("", response_model=AttachmentResponse)
async def create_attachment(
    task_id: str,
    attachment: AttachmentCreate,
    db: AsyncSession,
):
    # Create attachment
    db_att = Attachment(task_id=task_id, **attachment.dict())
    db.add(db_att)
    await db.commit()
    await db.refresh(db_att)

    # Re-index parent task (to include attachment content)
    task = await get_task_or_404(task_id, db)
    task_dict = task_to_dict(task)
    await rag_service.index_task(task_dict)

    return AttachmentResponse.from_orm(db_att)
```

### Dependency Installation

```bash
# Install dependencies
uv add chromadb sentence-transformers numpy
```

## Acceptance Criteria

- [ ] `EmbeddingService` generates 384-dimension embeddings
- [ ] `RAGService` creates ChromaDB collection on first use
- [ ] Task indexing works on create/update
- [ ] Attachment content is included in parent task's document
- [ ] Batch indexing processes multiple tasks efficiently
- [ ] Task deletion removes document from ChromaDB
- [ ] ChromaDB data persists to `settings.vector_store_path` (default: `~/.taskgenie/data/chroma`)
- [ ] Unit tests cover embedding generation and indexing
- [ ] Automated tests cover persistence + indexing + batch behavior (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Test Plan

### Automated

**Embedding Service Tests**
```python
# tests/test_services/test_embedding_service.py
import pytest
import numpy as np

class TestEmbeddingService:
    def test_generate_returns_correct_dimension(self):
        """Embedding has correct dimension."""
        from backend.services.embedding_service import embedding_service

        embedding = embedding_service.generate("Hello world")

        assert len(embedding) == 384
        assert all(isinstance(v, float) for v in embedding)

    def test_generate_deterministic(self):
        """Same text produces same embedding."""
        embedding_service = EmbeddingService()

        emb1 = embedding_service.generate("Test task")
        emb2 = embedding_service.generate("Test task")

        assert np.array_equal(emb1, emb2)

    def test_similarity_calculation(self):
        """Similarity calculation is correct."""
        from backend.services.embedding_service import embedding_service

        # Same text should have similarity ~1.0
        emb1 = embedding_service.generate("authentication bug")
        emb2 = embedding_service.generate("authentication bug")
        sim = embedding_service.similarity(emb1, emb2)
        assert sim > 0.99

        # Similar texts should have high similarity
        emb3 = embedding_service.generate("login auth issue")
        sim_similar = embedding_service.similarity(emb1, emb3)
        assert sim_similar > 0.5
```

**Indexing Tests**
```python
# tests/test_services/test_rag_indexing.py
import pytest

class TestRAGServiceIndexing:
    @pytest.mark.asyncio
    async def test_index_task(self, rag_service_test, mock_embedding_service):
        """Index a single task."""
        rag_service_test._embedding_service = mock_embedding_service

        task = {
            "id": "task-1",
            "title": "Fix auth",
            "description": "JWT token validation",
            "status": "pending",
        }

        await rag_service_test.index_task(task)

        # Verify in collection
        stored = rag_service_test.collection.get(ids=["task-1"])
        assert len(stored["ids"]) == 1
        assert "authentication" in stored["documents"][0].lower()

    @pytest.mark.asyncio
    async def test_index_task_with_attachments(self, rag_service_test, mock_embedding_service):
        """Task with attachments indexes correctly."""
        rag_service_test._embedding_service = mock_embedding_service

        task = {
            "id": "task-2",
            "title": "Review PR",
            "attachments": [
                {"title": "GitHub PR", "content": "Security fix"},
                {"title": "Gmail", "content": "Urgent issue"},
            ],
        }

        await rag_service_test.index_task(task)

        stored = rag_service_test.collection.get(ids=["task-2"])
        document = stored["documents"][0]
        assert "GitHub" in document
        assert "Security fix" in document
        assert stored["metadatas"][0]["has_attachments"] is True

    @pytest.mark.asyncio
    async def test_batch_indexing(self, rag_service_test, mock_embedding_service):
        """Batch indexing processes multiple tasks."""
        rag_service_test._embedding_service = mock_embedding_service

        tasks = [
            {"id": "1", "title": "Task 1"},
            {"id": "2", "title": "Task 2"},
            {"id": "3", "title": "Task 3"},
        ]

        ids = await rag_service_test.index_tasks_batch(tasks)

        assert ids == ["1", "2", "3"]

        stored = rag_service_test.collection.get()
        assert len(stored["ids"]) == 3
```

### Manual

1. Create a task via API
2. Check vector store directory exists (default: `~/.taskgenie/data/chroma`)
3. Verify task is indexed:
   ```python
   from backend.services.rag_service import rag_service

   collection = rag_service.collection
   result = collection.get()
   print(result)
   ```
4. Create task with attachment
5. Verify attachment content is in document
6. Delete task
7. Verify task is removed from ChromaDB

### Manual Test Checklist

- [ ] Vector store directory is created lazily (not at import time) and persists across restarts.
- [ ] Task create/update triggers indexing; delete removes documents.
- [ ] Attachment content contributes to the indexed document for its parent task.
- [ ] Batch indexing produces the expected number of stored documents.
- [ ] Embedding dimension is stable (384) and similarity behaves as expected.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Should we use a larger embedding model for better quality (`all-mpnet-base-v2`)?
- Should we embed title and description separately for better retrieval?
- How to handle re-indexing after attachment content changes?

## Dependencies

- PR-001 (DB + Config)
- PR-004 (Attachments)
- `chromadb`: `uv add chromadb`
- `sentence-transformers`: `uv add sentence-transformers`

## Next PRs

- **PR-005-2**: Semantic Search API + RAG Context (uses this indexing)
