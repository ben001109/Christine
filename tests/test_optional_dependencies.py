from christine.runtime.optional_dependencies import (
    OptionalDependencyStatus,
    check_ollama_service,
    check_optional_module,
    check_optional_service,
    optional_dependency_report,
    render_optional_dependency_diagnostics,
)


def test_check_optional_module_uses_injected_finder_without_importing_module():
    calls = []

    def finder(name):
        calls.append(name)
        return object() if name == "torch" else None

    status = check_optional_module("torch", purpose="GPU acceleration", finder=finder)

    assert status == OptionalDependencyStatus("torch", True, "GPU acceleration", "available")
    assert calls == ["torch"]


def test_check_optional_module_reports_missing_dependency():
    status = check_optional_module("pynput", purpose="global hotkeys", finder=lambda name: None)

    assert status.name == "pynput"
    assert status.available is False
    assert status.message == "missing"


def test_check_optional_service_uses_injected_checker():
    status = check_optional_service("ollama", purpose="local LLM", checker=lambda: (False, "connection refused"))

    assert status.name == "ollama"
    assert status.available is False
    assert status.message == "connection refused"


def test_check_ollama_service_reports_available_with_injected_opener():
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def opener(url, timeout):
        calls.append((url, timeout))
        return Response()

    status = check_ollama_service(opener=opener, timeout=0.2)

    assert status == OptionalDependencyStatus("ollama", True, "local LLM", "reachable")
    assert calls == [("http://127.0.0.1:11434/api/tags", 0.2)]


def test_check_ollama_service_reports_connection_failure():
    def opener(url, timeout):
        raise OSError("connection refused")

    status = check_ollama_service(opener=opener, timeout=0.2)

    assert status.name == "ollama"
    assert status.available is False
    assert status.message == "connection refused"


def test_render_optional_dependency_diagnostics_marks_degraded_dependencies():
    lines = render_optional_dependency_diagnostics(
        (
            OptionalDependencyStatus("torch", False, "GPU acceleration", "missing"),
            OptionalDependencyStatus("ollama", True, "local LLM", "reachable"),
        ),
        colors=False,
    )

    text = "\n".join(lines)
    assert "[Optional Dependencies]" in text
    assert "torch" in text
    assert "missing" in text
    assert "GPU acceleration" in text
    assert "ollama" in text
    assert "reachable" in text


def test_optional_dependency_report_contains_startup_diagnostics():
    report = optional_dependency_report(
        finder=lambda name: object() if name == "torch" else None,
        service_checkers={"ollama": lambda: (False, "connection refused")},
    )
    by_name = {status.name: status for status in report}

    assert set(by_name) == {"torch", "pynput", "sentence_transformers", "ollama"}
    assert by_name["torch"].available is True
    assert by_name["pynput"].available is False
    assert by_name["sentence_transformers"].available is False
    assert by_name["ollama"].message == "connection refused"


def test_runtime_exports_optional_dependency_status_api():
    from christine.runtime import OptionalDependencyStatus, optional_dependency_report

    assert OptionalDependencyStatus.__name__ == "OptionalDependencyStatus"
    assert callable(optional_dependency_report)
