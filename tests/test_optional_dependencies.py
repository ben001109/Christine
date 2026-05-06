from christine.runtime.optional_dependencies import (
    OptionalDependencyStatus,
    check_optional_module,
    check_optional_service,
    optional_dependency_report,
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
