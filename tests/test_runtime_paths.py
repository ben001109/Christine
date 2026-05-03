from christine.runtime.paths import RuntimePaths


def test_runtime_paths_keep_state_in_repo_root(tmp_path):
    paths = RuntimePaths.from_root(tmp_path)

    assert paths.data == tmp_path / "data"
    assert paths.logs == tmp_path / "level5_logs"
    assert paths.growth_log == tmp_path / "growth.log"
    assert paths.heartbeat == tmp_path / "heartbeat.txt"
    assert paths.nexus_state == tmp_path / "nexus_v2_state.json"
