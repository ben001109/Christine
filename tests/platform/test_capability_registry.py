from christine.platform.registry import capability_mapping, platform_identity
from christine.platform.base import PlatformFeature, capability_matrix


def test_platform_identity_normalizes_supported_runtime_names():
    assert platform_identity("win32").name == "windows"
    assert platform_identity("darwin").name == "macos"
    assert platform_identity("linux").name == "linux"


def test_unknown_identity_does_not_preserve_input_content():
    assert platform_identity("untrusted-platform-value").to_dict() == {"name": "unknown"}


def test_capability_mapping_has_only_declared_boolean_flags():
    capabilities = capability_mapping(platform_identity("win32"))

    assert set(capabilities) == {"autostart", "global_hotkeys", "system_audio", "gui", "tts", "local_llm"}
    assert all(type(value) is bool for value in capabilities.values())
    assert capabilities["autostart"] is True


def test_capability_mapping_matches_the_declared_matrix_for_all_normalized_identities():
    normalized_inputs = {"win32": "windows", "darwin": "macos", "linux": "linux", "plan9": "unknown"}
    matrix = capability_matrix()

    for sys_platform, identity_name in normalized_inputs.items():
        expected = {feature.value: support.supported for feature, support in matrix[identity_name].items()}

        assert dict(capability_mapping(platform_identity(sys_platform))) == expected
        assert set(expected) == {feature.value for feature in PlatformFeature}
