import datetime

from task_store import TaskStore, make_task, make_step


class TestTaskStoreNextId:
    def test_first_id_format(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        today = datetime.date(2026, 6, 12)
        sid = store.next_id(when=today)
        assert sid == "TSK-2026-0612-001"

    def test_increments_same_day(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        today = datetime.date(2026, 6, 12)
        store.create(goal="Test", role="coder", when=today)
        assert store.next_id(when=today) == "TSK-2026-0612-002"

    def test_independent_across_days(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        store.create(goal="Old", role="coder", when=datetime.date(2026, 6, 10))
        assert store.next_id(when=datetime.date(2026, 6, 12)) == "TSK-2026-0612-001"


class TestTaskStoreCreate:
    def test_creates_task(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Build feature X", role="coder")
        assert t["goal"] == "Build feature X"
        assert t["role"] == "coder"
        assert t["status"] == "pending"
        assert t["steps"] == []

    def test_persists_to_disk(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Test", role="researcher")
        assert (tmp_path / f"{t['id']}.yaml").exists()

    def test_with_session_id(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Test", role="coder", session_id="SES-2026-0612-001")
        assert t["session_id"] == "SES-2026-0612-001"

    def test_creates_with_role(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Research X", role="researcher")
        assert t["role"] == "researcher"


class TestTaskStoreGet:
    def test_get_returns_task(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Readable", role="coder")
        fetched = store.get(t["id"])
        assert fetched is not None
        assert fetched["goal"] == "Readable"

    def test_get_missing_returns_none(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        assert store.get("TSK-2099-0101-001") is None


class TestTaskStoreList:
    def test_list_all_empty(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        assert store.list_all() == []

    def test_list_all_returns_all(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        store.create(goal="A", role="coder")
        store.create(goal="B", role="researcher")
        assert len(store.list_all()) == 2

    def test_list_by_status(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t1 = store.create(goal="Active", role="coder")
        t2 = store.create(goal="Done", role="coder")
        store.update_status(t2["id"], "completed")
        pending = store.list_by_status("pending")
        completed = store.list_by_status("completed")
        assert len(pending) == 1
        assert pending[0]["id"] == t1["id"]
        assert len(completed) == 1
        assert completed[0]["id"] == t2["id"]


class TestTaskStoreSteps:
    def test_add_step(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Step test", role="coder")
        step = make_step(
            action="read config",
            tool_name="read_file",
            tool_params={"path": "/tmp/config.yaml"},
            observation="Found config",
        )
        updated = store.add_step(t["id"], step)
        assert len(updated["steps"]) == 1
        assert updated["steps"][0]["action"] == "read config"
        assert updated["steps"][0]["tool_name"] == "read_file"

    def test_add_step_missing_task(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        assert store.add_step("TSK-2099-0101-001", make_step(action="x")) is None

    def test_add_multiple_steps(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Multi-step", role="coder")
        store.add_step(t["id"], make_step(action="step 1"))
        store.add_step(t["id"], make_step(action="step 2"))
        updated = store.get(t["id"])
        assert len(updated["steps"]) == 2


class TestTaskStoreStatus:
    def test_update_status(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Status test", role="coder")
        updated = store.update_status(t["id"], "in_progress")
        assert updated["status"] == "in_progress"
        fetched = store.get(t["id"])
        assert fetched["status"] == "in_progress"

    def test_update_status_missing(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        assert store.update_status("TSK-2099-0101-001", "done") is None

    def test_set_result(self, tmp_path):
        store = TaskStore(base_dir=tmp_path)
        t = store.create(goal="Result test", role="synthesizer")
        updated = store.set_result(t["id"], "Generated report")
        assert updated["result"] == "Generated report"


class TestMakeTask:
    def test_make_task_fields(self):
        t = make_task("TSK-2026-0612-001", "Build X", "coder")
        assert t["id"] == "TSK-2026-0612-001"
        assert t["goal"] == "Build X"
        assert t["role"] == "coder"
        assert t["status"] == "pending"
        assert "created" in t
        assert t["result"] is None


class TestMakeStep:
    def test_make_step_minimal(self):
        s = make_step(action="read file")
        assert s["action"] == "read file"
        assert s["tool_name"] is None
        assert "timestamp" in s

    def test_make_step_full(self):
        s = make_step(
            action="search web",
            tool_name="web_search",
            tool_params={"query": "AIOS"},
            observation="Found 3 results",
        )
        assert s["tool_name"] == "web_search"
        assert s["tool_params"] == {"query": "AIOS"}
        assert s["observation"] == "Found 3 results"
