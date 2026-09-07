from tools.memory_tools import read_memory, write_memory


def test_memory_round_trip(lab_root):
    runtime = lab_root / "environment" / "runtime"
    write_memory(runtime, "room", "A", "user")
    assert read_memory(runtime, "room")["entry"]["value"] == "A"
