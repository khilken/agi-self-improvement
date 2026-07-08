# Hermes Deep Analysis & Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every Hermes module actually run, fix all identified defects with tests, then improve efficiency — finishing with a knowledge-graph dashboard.

**Architecture:** Hermes is a file-backed multi-agent scaffold: `vector_memory/` (ChromaDB + Ollama embeddings), `mcp/` (file-queue message protocol), `tasks/` (JSON task queue), `agents/memory_synthesizer.py` (consumer agent), `memory_dashboard/` (HTML + exporter + HTTP server). Fixes keep this architecture; no rewrites.

**Tech Stack:** Python 3.11+, ChromaDB, ollama client, numpy, scikit-learn, pytest. hdbscan/umap-learn are optional (code has fallbacks; tests must pass without them and without Ollama running).

## Global Constraints

- Repo root: `/Users/kevin/Library/CloudStorage/OneDrive-Personal/AI/Hermes/self` — all commands run from here unless stated.
- Virtualenv lives OUTSIDE OneDrive at `~/.venvs/hermes`. Python binary: `~/.venvs/hermes/bin/python`, pytest: `~/.venvs/hermes/bin/pytest`.
- Never modify or delete anything under `memory/vector_db/` (live data).
- Tests must not require Ollama to be running, or hdbscan/umap-learn to be installed.
- All list-valued metadata going into ChromaDB must be serialized (comma-joined string for tags, JSON string for id lists) — ChromaDB only accepts str/int/float/bool.
- Commit after every task with a descriptive message.

---

### Task 1: Environment setup + baseline audit

**Files:**
- Create: `~/.venvs/hermes` (venv, outside repo)
- Create: `requirements.txt`
- Create: `tests/__init__.py` (empty)
- Create: `conftest.py` (empty — makes repo root importable by pytest)

**Interfaces:**
- Produces: working venv all later tasks use via `~/.venvs/hermes/bin/python`.

- [ ] **Step 1: Create venv and requirements.txt**

`requirements.txt`:
```
chromadb>=0.5
ollama>=0.3
numpy>=1.26
scikit-learn>=1.4
pytest>=8
```

```bash
python3 -m venv ~/.venvs/hermes
~/.venvs/hermes/bin/pip install -r requirements.txt
```
Expected: install succeeds.

- [ ] **Step 2: Baseline import audit**

```bash
cd "/Users/kevin/Library/CloudStorage/OneDrive-Personal/AI/Hermes/self"
~/.venvs/hermes/bin/python -c "import vector_memory; import mcp.protocol; import tasks.task_queue; import agents.memory_synthesizer" 
```
Expected: may fail or warn — record exact output in commit message body. (agents/ has no `__init__.py`; import via `python agents/memory_synthesizer.py --help` style instead if needed. Record what happens.)

- [ ] **Step 3: Create empty `tests/__init__.py` and `conftest.py`, commit**

```bash
git add requirements.txt tests/__init__.py conftest.py
git commit -m "chore: add venv requirements and test scaffolding; record baseline audit"
```

---

### Task 2: Anchor all filesystem paths to the repo root

**Files:**
- Modify: `tasks/task_queue.py:38-39`
- Modify: `mcp/protocol.py:102, 289`
- Modify: `memory_dashboard/schedule_memory_export.py:24-26`
- Modify: `vector_memory/vector_memory.py:67, 72-73, 293`
- Test: `tests/test_task_queue.py`

**Interfaces:**
- Produces: every module works regardless of CWD. `tasks.task_queue.TASKS_DIR` remains a module-level `Path` (tests monkeypatch it).

- [ ] **Step 1: Write failing test**

`tests/test_task_queue.py`:
```python
import json
from tasks import task_queue


def test_create_claim_complete_cycle(tmp_path, monkeypatch):
    monkeypatch.setattr(task_queue, "TASKS_DIR", tmp_path)
    tid = task_queue.create_task("full_synthesis", source="test", payload={"x": 1})
    pending = task_queue.list_pending_tasks()
    assert [t["id"] for t in pending] == [tid]
    assert task_queue.claim_task(tid) is True
    assert task_queue.claim_task(tid) is False  # already claimed
    assert task_queue.complete_task(tid, {"ok": True}) is True
    task = task_queue.get_task(tid)
    assert task["status"] == "completed"
    assert task["result"] == {"ok": True}
    assert task_queue.list_pending_tasks() == []


def test_pending_tasks_sorted_oldest_first(tmp_path, monkeypatch):
    monkeypatch.setattr(task_queue, "TASKS_DIR", tmp_path)
    ids = [task_queue.create_task(f"t{i}") for i in range(3)]
    # Force distinct created_at ordering
    for i, tid in enumerate(ids):
        p = tmp_path / f"{tid}.json"
        t = json.loads(p.read_text())
        t["created_at"] = 100 + i
        p.write_text(json.dumps(t))
    pending = task_queue.list_pending_tasks()
    assert [t["id"] for t in pending] == ids


def test_tasks_dir_is_absolute():
    assert task_queue.TASKS_DIR.is_absolute()
```

- [ ] **Step 2: Run to verify failure**

Run: `~/.venvs/hermes/bin/pytest tests/test_task_queue.py -v`
Expected: `test_tasks_dir_is_absolute` FAILS (`Path("tasks")` is relative). Others should pass.

- [ ] **Step 3: Anchor paths**

`tasks/task_queue.py` — replace lines 38-39:
```python
TASKS_DIR = Path(__file__).resolve().parent
```
(The directory already exists — remove the `mkdir` call.)

`mcp/protocol.py` — `FileTransport.__init__` default (line 102):
```python
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).resolve().parent / "queues"
```
`AgentRegistry.__init__` default (line 289):
```python
    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path(__file__).resolve().parent / "registry.json"
```

`vector_memory/vector_memory.py` — add after logger (line 28):
```python
HERMES_ROOT = Path(__file__).resolve().parent.parent
```
Change `__init__` default `persist_directory: str = "memory/vector_db"` to `persist_directory: Optional[str] = None`, and in the body:
```python
        self.persist_directory = Path(persist_directory) if persist_directory else HERMES_ROOT / "memory" / "vector_db"
```
In `get_vector_memory` change `config.get("vector_db_path", "memory/vector_db")` to `config.get("vector_db_path")`.

`memory_dashboard/schedule_memory_export.py` — replace lines 24-26:
```python
HERMES_ROOT = Path(__file__).resolve().parent.parent
EXPORT_INTERVAL_SECONDS = 300          # 5 minutes (change as needed)
EXPORT_SCRIPT = str(HERMES_ROOT / "memory_dashboard" / "export_memory_stats.py")
LOG_FILE = str(HERMES_ROOT / "memory_dashboard" / "export.log")
```
(and in `run_export`, `cwd=HERMES_ROOT`).

- [ ] **Step 4: Run tests**

Run: `~/.venvs/hermes/bin/pytest tests/test_task_queue.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add tasks/task_queue.py mcp/protocol.py vector_memory/vector_memory.py memory_dashboard/schedule_memory_export.py tests/test_task_queue.py
git commit -m "fix: anchor all filesystem paths to repo root instead of CWD"
```

---

### Task 3: VectorMemory — ChromaDB-legal metadata, no random embeddings, no mutable default

**Files:**
- Modify: `vector_memory/vector_memory.py`
- Test: `tests/test_vector_memory.py`

**Interfaces:**
- Produces: `_sanitize_metadata(meta: Dict) -> Dict` module-level function in `vector_memory/vector_memory.py` (lists → comma-joined strings; dicts → JSON strings; None values dropped). Task 4 and Task 6 rely on it.
- `_get_embedding` now raises `RuntimeError` when no embedding backend works.

- [ ] **Step 1: Write failing tests**

`tests/test_vector_memory.py`:
```python
import pytest
from vector_memory import VectorMemory
from vector_memory.vector_memory import _sanitize_metadata


@pytest.fixture
def vm(tmp_path, monkeypatch):
    mem = VectorMemory(persist_directory=str(tmp_path), collection_name="test")
    # Deterministic fake embeddings — no Ollama needed
    monkeypatch.setattr(mem, "_get_embedding", lambda text: [float(len(text) % 7)] * 8)
    return mem


def test_sanitize_metadata_serializes_lists():
    out = _sanitize_metadata({"tags": ["a", "b"], "n": 3, "ids": ["x"], "none": None})
    assert out["tags"] == "a,b"
    assert out["n"] == 3
    assert out["ids"] == "x"
    assert "none" not in out


def test_add_reflection_with_tags_roundtrips(vm):
    item_id = vm.add_reflection("insight", project="p1", tags=["alpha", "beta"])
    got = vm.collection.get(ids=[item_id])
    assert got["metadatas"][0]["tags"] == "alpha,beta"


def test_add_and_query(vm):
    vm.add("hello world", metadata={"project": "p1"})
    res = vm.query("hello world", n_results=1)
    assert res["documents"][0][0] == "hello world"


def test_embedding_failure_raises(tmp_path):
    mem = VectorMemory(persist_directory=str(tmp_path), collection_name="t2")
    import vector_memory.vector_memory as vmod
    orig = vmod.OLLAMA_AVAILABLE
    vmod.OLLAMA_AVAILABLE = False
    try:
        with pytest.raises(RuntimeError):
            mem._get_embedding("text")
    finally:
        vmod.OLLAMA_AVAILABLE = orig
```

- [ ] **Step 2: Run to verify failure**

Run: `~/.venvs/hermes/bin/pytest tests/test_vector_memory.py -v`
Expected: FAIL — `_sanitize_metadata` doesn't exist; `add_reflection` raises ChromaDB ValueError on list tags; `_get_embedding` returns random instead of raising.

- [ ] **Step 3: Implement**

In `vector_memory/vector_memory.py`:

Add module-level function (after `MemoryItem`):
```python
def _sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """ChromaDB metadata values must be str/int/float/bool. Lists become
    comma-joined strings, dicts become JSON, None entries are dropped."""
    clean: Dict[str, Any] = {}
    for key, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        elif isinstance(value, (list, tuple)):
            clean[key] = ",".join(str(v) for v in value)
        elif isinstance(value, dict):
            clean[key] = json.dumps(value, default=str)
        else:
            clean[key] = str(value)
    return clean
```

In `add()` (line 137) change `meta = metadata or {}` to:
```python
        meta = _sanitize_metadata(metadata or {})
```
In `add_many()` (line 162) change `meta = item.get("metadata", {})` to:
```python
            meta = _sanitize_metadata(item.get("metadata", {}))
```

Replace `_get_embedding` fallbacks — both `random` blocks become:
```python
        raise RuntimeError(
            "No embedding backend available. Install and run Ollama, then: "
            f"ollama pull {self.embedding_model}"
        )
```
(keep the Ollama try/except; on exception re-raise as RuntimeError with the original error message instead of falling back to random).

Fix mutable default in `query()` (line 185):
```python
        include: Optional[List[str]] = None,
```
and in the body:
```python
        include = include or ["documents", "metadatas", "distances"]
```

- [ ] **Step 4: Run tests**

Run: `~/.venvs/hermes/bin/pytest tests/test_vector_memory.py tests/test_task_queue.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add vector_memory/vector_memory.py tests/test_vector_memory.py
git commit -m "fix: ChromaDB-legal metadata, raise on missing embeddings, no mutable default"
```

---

### Task 4: Semantic clustering — numpy truthiness crash, O(n²) centroids, metadata lists

**Files:**
- Modify: `vector_memory/semantic_clustering.py:113-118, 179-184, 296-307`
- Test: `tests/test_semantic_clustering.py`

**Interfaces:**
- Consumes: `_sanitize_metadata` behavior via `vm.add` (Task 3 already sanitizes inside `add`, so `cluster_and_synthesize` needs no explicit call — just verify).
- Produces: `cluster_memories` returns `List[SemanticCluster]` and never evaluates array truthiness.

- [ ] **Step 1: Write failing test**

`tests/test_semantic_clustering.py`:
```python
import numpy as np
import pytest
from vector_memory import VectorMemory, SemanticClustering


@pytest.fixture
def vm(tmp_path):
    return VectorMemory(persist_directory=str(tmp_path), collection_name="clus")


def _seed(vm, n=12):
    # Two well-separated synthetic groups of embeddings
    for i in range(n):
        group = i % 2
        emb = list(np.full(8, float(group * 10)) + np.random.RandomState(i).rand(8) * 0.1)
        vm.collection.add(
            ids=[f"m{i}"], documents=[f"doc {i}"],
            metadatas=[{"type": "note"}], embeddings=[emb],
        )


def test_cluster_memories_empty_collection(vm):
    # Regression: numpy-array truthiness must not raise
    assert vm.count() == 0
    assert SemanticClustering(vm).cluster_memories(n_results=10) == []


def test_cluster_memories_groups(vm):
    _seed(vm)
    clusters = SemanticClustering(vm).cluster_memories(
        n_results=50, min_cluster_size=3, use_umap=False
    )
    assert isinstance(clusters, list)
    total = sum(c.size for c in clusters)
    assert 0 < total <= 12
    for c in clusters:
        assert c.centroid is not None
        assert len(c.member_ids) == c.size
```

- [ ] **Step 2: Run to verify failure**

Run: `~/.venvs/hermes/bin/pytest tests/test_semantic_clustering.py -v`
Expected: `test_cluster_memories_empty_collection` FAILS with `ValueError: The truth value of an array with more than one element is ambiguous` (or returns non-[] depending on chromadb version).

- [ ] **Step 3: Implement**

`semantic_clustering.py` lines 113-115, replace:
```python
        raw_embeddings = data.get("embeddings")
        if raw_embeddings is None or len(raw_embeddings) == 0:
            logger.warning("No embeddings found for clustering.")
            return []

        embeddings = np.array(raw_embeddings)
```

Replace the O(n²) centroid block (lines 158-184) — group indices while iterating labels, then average once:
```python
        clusters: Dict[int, SemanticCluster] = {}
        cluster_indices: Dict[int, List[int]] = {}
        noise_label = -1

        for i, label in enumerate(labels):
            if label == noise_label:
                continue
            if label not in clusters:
                clusters[label] = SemanticCluster(
                    cluster_id=int(label),
                    member_ids=[], member_documents=[], member_metadatas=[],
                    size=0,
                )
                cluster_indices[label] = []
            clusters[label].member_ids.append(ids[i])
            clusters[label].member_documents.append(documents[i])
            clusters[label].member_metadatas.append(metadatas[i] if metadatas is not None else {})
            clusters[label].size += 1
            cluster_indices[label].append(i)

        for label, cluster in clusters.items():
            cluster.centroid = np.mean(reduced_embeddings[cluster_indices[label]], axis=0)
```

In `cluster_and_synthesize` (lines 296-307): the `vm.add` call now sanitizes metadata (Task 3), so `tags` and `member_ids` lists are safe — no change needed, but keep `"member_ids": ",".join(cluster.member_ids[:10])` explicit for readability:
```python
                            "member_ids": ",".join(cluster.member_ids[:10]),
```

- [ ] **Step 4: Run tests**

Run: `~/.venvs/hermes/bin/pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add vector_memory/semantic_clustering.py tests/test_semantic_clustering.py
git commit -m "fix: clustering numpy truthiness crash and O(n^2) centroid computation"
```

---

### Task 5: MCP protocol — correlation IDs and duplicate sends

**Files:**
- Modify: `mcp/protocol.py:228-241, 339-352`
- Test: `tests/test_mcp_protocol.py`

**Interfaces:**
- Produces: `delegate_task` sets `correlation_id` to the request's own `message_id`; `process_inbox` returns handler responses that have NOT been sent yet (error replies are sent inside and not returned).

- [ ] **Step 1: Write failing test**

`tests/test_mcp_protocol.py`:
```python
from mcp.protocol import MCPProtocol, MessageType, FileTransport


def _pair(tmp_path):
    transport = FileTransport(base_path=tmp_path)
    return (MCPProtocol("hermes", transport=transport),
            MCPProtocol("worker", transport=transport))


def test_delegate_task_sets_correlation_id(tmp_path):
    hermes, worker = _pair(tmp_path)
    req = hermes.delegate_task("worker", "do thing", {"project": "p"})
    inbox = worker.receive()
    assert len(inbox) == 1
    assert inbox[0].correlation_id == req.message_id


def test_report_result_roundtrip(tmp_path):
    hermes, worker = _pair(tmp_path)
    req = hermes.delegate_task("worker", "do thing", {})
    msg = worker.receive()[0]
    worker.report_result("hermes", msg.correlation_id, {"answer": 42})
    results = hermes.receive()
    assert len(results) == 1
    assert results[0].correlation_id == req.message_id
    assert results[0].payload["result"] == {"answer": 42}


def test_handler_error_reply_sent_once(tmp_path):
    hermes, worker = _pair(tmp_path)

    def boom(msg):
        raise RuntimeError("boom")

    worker.register_handler(MessageType.TASK_REQUEST, boom)
    hermes.delegate_task("worker", "explode", {})
    responses = worker.process_inbox()
    # Error reply already sent inside process_inbox — must not be returned
    # for a second send by run_loop.
    assert responses == []
    errors = hermes.receive()
    assert len(errors) == 1
    assert errors[0].message_type == MessageType.ERROR
```

- [ ] **Step 2: Run to verify failure**

Run: `~/.venvs/hermes/bin/pytest tests/test_mcp_protocol.py -v`
Expected: `test_delegate_task_sets_correlation_id` FAILS (correlation_id is None); `test_handler_error_reply_sent_once` FAILS (responses contains the already-sent error).

- [ ] **Step 3: Implement**

`delegate_task` — build the message so correlation_id equals its own message_id:
```python
    def delegate_task(self, to_agent: str, task_description: str, context: Dict[str, Any],
                      priority: int = 3) -> MCPMessage:
        """High-level helper to delegate work to a sub-agent."""
        msg = MCPMessage(
            from_agent=self.agent_name,
            to_agent=to_agent,
            message_type=MessageType.TASK_REQUEST,
            payload={
                "task": task_description,
                "context": context,
                "requested_by": self.agent_name,
            },
            priority=priority,
            tags=["delegation"],
        )
        msg.correlation_id = msg.message_id
        self.transport.send(msg)
        return msg
```

`process_inbox` — the error branch already sends; stop appending it:
```python
                except Exception as e:
                    logger.exception(f"Handler error for {msg.message_type}: {e}")
                    self.send(
                        to_agent=msg.from_agent,
                        msg_type=MessageType.ERROR,
                        payload={"error": str(e), "original_message_id": msg.message_id},
                        correlation_id=msg.correlation_id
                    )
```

`BaseMCPAgent.run_loop` — responses returned by handlers are unsent messages the agent wants delivered; keep the send but drop the broadcast exclusion asymmetry only if trivial. Final loop body:
```python
                responses = self.mcp.process_inbox()
                for r in responses:
                    self.mcp.transport.send(r)
```
(Also apply the same two-line change in `agents/memory_synthesizer.py` `run_loop`, lines 373-376.)

- [ ] **Step 4: Run tests**

Run: `~/.venvs/hermes/bin/pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp/protocol.py agents/memory_synthesizer.py tests/test_mcp_protocol.py
git commit -m "fix: MCP correlation IDs on delegation and duplicate error sends"
```

---

### Task 6: MemorySynthesizer honesty — real archiving, stored importance scores

**Files:**
- Modify: `agents/memory_synthesizer.py:139-169, 208-226`
- Create: `agents/__init__.py` (empty, so tests can import)
- Test: `tests/test_memory_synthesizer.py`

**Interfaces:**
- Consumes: `VectorMemory` (Task 3), monkeypatched `_llm_summarize` in tests.
- Produces: `_run_full_synthesis` marks originals with metadata `{"archived": True}` via `collection.update`; `_run_importance_scoring` stores `{"importance": <float>}` via `collection.update`.

- [ ] **Step 1: Write failing test**

`tests/test_memory_synthesizer.py`:
```python
import pytest
from vector_memory import VectorMemory


@pytest.fixture
def agent(tmp_path, monkeypatch):
    import mcp.protocol as proto
    from mcp.protocol import FileTransport
    # Isolate MCP + registry side effects
    monkeypatch.setattr(proto.AgentRegistry, "__init__",
                        lambda self, path=None: setattr(self, "path", tmp_path / "reg.json") or self._write({}))
    from agents.memory_synthesizer import MemorySynthesizerAgent
    monkeypatch.setattr(
        "agents.memory_synthesizer.MemorySynthesizerAgent.__init__",
        _patched_init(tmp_path), raising=True,
    )
    return MemorySynthesizerAgent()


def _patched_init(tmp_path):
    from mcp.protocol import MCPProtocol, FileTransport, MessageType

    def init(self, name="memory_synthesizer"):
        self.name = name
        self.mcp = MCPProtocol(name, transport=FileTransport(base_path=tmp_path / "q"))
        self.vm = VectorMemory(persist_directory=str(tmp_path / "db"), collection_name="syn")
        self.vm._get_embedding = lambda text: [float(len(text) % 5)] * 8
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)
    return init


def test_full_synthesis_archives_originals(agent, monkeypatch):
    long_doc = "x" * 900
    item_id = agent.vm.add(long_doc, metadata={"type": "reflection"})
    monkeypatch.setattr(agent, "_llm_summarize", lambda text, meta: "short summary")
    result = agent._run_full_synthesis({})
    assert result["status"] == "success"
    assert result["synthesized_count"] == 1
    original = agent.vm.collection.get(ids=[item_id])
    assert original["metadatas"][0].get("archived") is True


def test_importance_scoring_persists(agent):
    item_id = agent.vm.add("a decision was made", metadata={"type": "reflection"})
    result = agent._run_importance_scoring({})
    assert result["status"] == "success"
    got = agent.vm.collection.get(ids=[item_id])
    assert got["metadatas"][0].get("importance") == pytest.approx(0.85)
```

- [ ] **Step 2: Run to verify failure**

Run: `~/.venvs/hermes/bin/pytest tests/test_memory_synthesizer.py -v`
Expected: FAIL — no `archived` metadata, no `importance` metadata.

- [ ] **Step 3: Implement**

In `_run_full_synthesis`, replace the synthesize block (lines 144-161):
```python
            if meta.get("type") in ["reflection", "research"] and len(doc) > 800:
                summary = self._llm_summarize(doc, meta)
                if summary and len(summary) < len(doc) * 0.6:
                    original_id = all_memories["ids"][i]
                    self.vm.add(
                        content=summary,
                        metadata={
                            **meta,
                            "type": "synthesized",
                            "original_id": original_id,
                            "synthesized_by": self.name,
                            "timestamp": time.time()
                        }
                    )
                    synthesized_count += 1

                    # Soft-archive the original so retrieval can filter it out
                    self.vm.collection.update(
                        ids=[original_id],
                        metadatas=[{**meta, "archived": True}]
                    )
                    archived_count += 1
```

In `_run_importance_scoring`, replace the loop (lines 215-220):
```python
        ids = memories.get("ids", [])
        metadatas = memories.get("metadatas", []) or []
        for i, doc in enumerate(memories.get("documents", [])):
            if not doc:
                continue
            meta = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
            score = self._llm_importance_score(doc, meta)
            self.vm.collection.update(
                ids=[ids[i]],
                metadatas=[{**meta, "importance": score}]
            )
            scored += 1
```

Create empty `agents/__init__.py`.

- [ ] **Step 4: Run tests**

Run: `~/.venvs/hermes/bin/pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/memory_synthesizer.py agents/__init__.py tests/test_memory_synthesizer.py
git commit -m "fix: actually archive synthesized originals and persist importance scores"
```

---

### Task 7: Wire dashboard buttons to the real task queue

**Files:**
- Modify: `memory_dashboard/run_dashboard_server.py`
- Modify: `memory_dashboard/memory_health_dashboard.html` (`writeTaskFile` function, ~line 558)
- Modify: `memory_dashboard/export_memory_stats.py` (tags-as-string counting, `sys.exit`)
- Test: `tests/test_dashboard_server.py`

**Interfaces:**
- Produces: `POST /api/task` with JSON body `{"task_type": "..."}` → creates a task via `tasks.task_queue.create_task(task_type, source="memory_health_dashboard")`, responds `201` with `{"task_id": "..."}`.

- [ ] **Step 1: Write failing test**

`tests/test_dashboard_server.py`:
```python
import json
import threading
import urllib.request
import socketserver
import pytest
from tasks import task_queue


def test_post_api_task_creates_task(tmp_path, monkeypatch):
    monkeypatch.setattr(task_queue, "TASKS_DIR", tmp_path)
    from memory_dashboard.run_dashboard_server import DashboardHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", 0), DashboardHTTPRequestHandler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/task",
                data=json.dumps({"task_type": "health_report"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                assert resp.status == 201
                body = json.loads(resp.read())
            task = task_queue.get_task(body["task_id"])
            assert task["task_type"] == "health_report"
            assert task["source"] == "memory_health_dashboard"
        finally:
            httpd.shutdown()
```

Also create empty `memory_dashboard/__init__.py` so the import works.

- [ ] **Step 2: Run to verify failure**

Run: `~/.venvs/hermes/bin/pytest tests/test_dashboard_server.py -v`
Expected: FAIL — 501 Unsupported method ('POST').

- [ ] **Step 3: Implement server endpoint**

`run_dashboard_server.py` — add imports and `do_POST` to the handler:
```python
import http.server
import json
import socketserver
import sys
from pathlib import Path

PORT = 8765
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY.parent))  # make tasks/ importable when run directly

from tasks.task_queue import create_task
```
Inside `DashboardHTTPRequestHandler`:
```python
    def do_POST(self):
        if self.path != "/api/task":
            self.send_error(404, "Unknown endpoint")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            task_type = body["task_type"]
        except (ValueError, KeyError):
            self.send_error(400, "Expected JSON body with 'task_type'")
            return
        task_id = create_task(task_type, source="memory_health_dashboard",
                              payload=body.get("payload"))
        response = json.dumps({"task_id": task_id}).encode()
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
```
Remove `os.chdir(DIRECTORY)` and the `os` import (handler already serves from `DIRECTORY`).

- [ ] **Step 4: Implement HTML side**

Replace `writeTaskFile` in `memory_health_dashboard.html`:
```javascript
        async function writeTaskFile(taskType) {
            try {
                const resp = await fetch('/api/task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_type: taskType })
                });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const data = await resp.json();
                console.log(`[Dashboard → Hermes] Task created: ${data.task_id} (${taskType})`);
            } catch (err) {
                console.error('[Dashboard] Failed to create task:', err);
                showToast('Failed to queue task — is the dashboard server running?');
            }
        }
```

- [ ] **Step 5: Fix export_memory_stats.py tag handling**

Tags are now stored as comma-joined strings (Task 3). Replace the tag loop (line 60-61):
```python
        raw_tags = meta.get("tags", "")
        tags = raw_tags.split(",") if isinstance(raw_tags, str) else list(raw_tags)
        for tag in (t.strip() for t in tags if t.strip()):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
```
And change `exit(1)` (line 25) to `raise SystemExit(1)`. Same for `recent_syntheses` field `"tags": meta.get("tags", [])` → keep as-is (string is fine for display) but split for consistency:
```python
                "tags": [t for t in str(meta.get("tags", "")).split(",") if t],
```

- [ ] **Step 6: Run tests**

Run: `~/.venvs/hermes/bin/pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add memory_dashboard/ tests/test_dashboard_server.py
git commit -m "feat: dashboard buttons create real tasks via POST /api/task"
```

---

### Task 8: Full-system verification + quality pass

**Files:**
- Modify: whatever the review pass finds (small diffs only)
- Modify: `README.md` if instructions no longer match reality

- [ ] **Step 1: Run the whole test suite**

Run: `~/.venvs/hermes/bin/pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 2: Execute every entry point from repo root**

```bash
cd "/Users/kevin/Library/CloudStorage/OneDrive-Personal/AI/Hermes/self"
~/.venvs/hermes/bin/python vector_memory/vector_memory.py
~/.venvs/hermes/bin/python mcp/protocol.py
~/.venvs/hermes/bin/python tasks/task_queue.py
~/.venvs/hermes/bin/python memory_dashboard/export_memory_stats.py
timeout 5 ~/.venvs/hermes/bin/python memory_dashboard/run_dashboard_server.py || true
```
Expected: each prints its banner without traceback (export may report clustering skipped if hdbscan absent — acceptable). The two agent loops (`memory_synthesizer.py`, `example_researcher_agent.py`) are verified by starting each with `timeout 5` and confirming clean startup logs, no traceback.

- [ ] **Step 3: Execute one end-to-end flow**

```bash
~/.venvs/hermes/bin/python - <<'EOF'
import sys; sys.path.insert(0, ".")
from tasks.task_queue import create_task, get_task, list_pending_tasks
tid = create_task("health_report", source="verification")
assert any(t["id"] == tid for t in list_pending_tasks())
print("task queue e2e OK:", tid)
EOF
```
Then clean up the verification task file it created (`rm tasks/<tid>.json`).

- [ ] **Step 4: Quality review pass**

Run the `/code-review` skill at medium effort over the accumulated diff (`git diff 596fd29..HEAD`). Apply confirmed findings, re-run `pytest tests/ -v`, expect PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: full-system verification and quality pass"
```

---

### Task 9: Knowledge-graph dashboard (Phase 5)

- [ ] **Step 1: Run `understand-anything:understand`** on the repaired repo (Skill tool, from repo root).
- [ ] **Step 2: Verify output** — graph generated, dashboard viewable; note the launch command for the user.
- [ ] **Step 3: Commit generated artifacts** if the skill writes them into the repo:
```bash
git add -A && git commit -m "docs: add knowledge graph of repaired Hermes architecture"
```
