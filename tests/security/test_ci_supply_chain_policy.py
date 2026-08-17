from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest
from unittest.mock import patch

from tools.check_ci_supply_chain import (
    POLICY_WORKFLOW,
    validate_policy_workflow,
    validate_repository,
    validate_workflow_text,
)


SHA = "a" * 40
DIGEST = "b" * 64
PINNED_CHECKOUT = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
MINIMAL_POLICY = f"""\
name: CI supply-chain policy

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  ci-supply-chain-policy:
    runs-on: ubuntu-24.04
    steps:
      - uses: {PINNED_CHECKOUT} # v4.4.0
      - run: python3 tools/check_ci_supply_chain.py
"""


def _workflow(*, uses: str = f"owner/action@{SHA}", container: str | None = None) -> str:
    container_line = f"    container: {container}\n" if container is not None else ""
    return f"""\
name: fixture
on: push
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-24.04
{container_line}    steps:
      - uses: {uses}
"""


class CiSupplyChainPolicyTests(unittest.TestCase):
    def assert_policy_rejected(self, text: str) -> None:
        self.assertTrue(validate_policy_workflow(text))

    def test_accepts_exact_minimal_policy_and_default_job_context(self):
        self.assertEqual(validate_workflow_text(MINIMAL_POLICY), ())
        self.assertEqual(validate_policy_workflow(MINIMAL_POLICY), ())
        job = MINIMAL_POLICY.split("  ci-supply-chain-policy:\n", 1)[1]
        self.assertNotIn("    name:", job)

    def test_repository_accepts_only_the_standalone_policy_workflow(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            workflow = root / POLICY_WORKFLOW
            workflow.parent.mkdir(parents=True)
            workflow.write_text(MINIMAL_POLICY, encoding="utf-8")
            with patch(
                "tools.check_ci_supply_chain.tracked_workflow_paths",
                return_value=(workflow,),
            ):
                self.assertEqual(validate_repository(root), ())

    def test_repository_fails_closed_on_discovery_and_missing_policy(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch(
                "tools.check_ci_supply_chain.tracked_workflow_paths",
                side_effect=subprocess.CalledProcessError(1, "git ls-files"),
            ):
                self.assertTrue(validate_repository(root))
            with patch("tools.check_ci_supply_chain.tracked_workflow_paths", return_value=()):
                self.assertTrue(validate_repository(root))
            missing = root / POLICY_WORKFLOW
            with patch(
                "tools.check_ci_supply_chain.tracked_workflow_paths",
                return_value=(missing,),
            ):
                self.assertTrue(validate_repository(root))

    def test_rejects_missing_renamed_duplicate_or_custom_named_policy_job(self):
        mutations = (
            MINIMAL_POLICY.replace("  ci-supply-chain-policy:\n", "", 1),
            MINIMAL_POLICY.replace("  ci-supply-chain-policy:\n", "  renamed-policy:\n", 1),
            MINIMAL_POLICY.replace(
                "  ci-supply-chain-policy:\n",
                "  ci-supply-chain-policy:\n  ci-supply-chain-policy:\n",
                1,
            ),
            MINIMAL_POLICY.replace(
                "    runs-on: ubuntu-24.04\n",
                "    name: ci-supply-chain-policy\n    runs-on: ubuntu-24.04\n",
                1,
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_policy_rejected(mutation)

    def test_rejects_missing_changed_duplicate_or_dynamic_command(self):
        command = "      - run: python3 tools/check_ci_supply_chain.py\n"
        mutations = (
            MINIMAL_POLICY.replace(command, "", 1),
            MINIMAL_POLICY.replace(command, "      - run: python tools/check_ci_supply_chain.py\n", 1),
            MINIMAL_POLICY.replace(command, command + command, 1),
            MINIMAL_POLICY.replace(command, "      - run: ${{ vars.POLICY_COMMAND }}\n", 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_policy_rejected(mutation)

    def test_accepts_full_sha_local_and_digest_pinned_docker_actions(self):
        references = (
            f"owner/action@{SHA}",
            "./.github/actions/local-check",
            f"docker://registry.example.test/team/check:1.2.3@sha256:{DIGEST}",
        )
        for reference in references:
            with self.subTest(reference=reference):
                self.assertEqual(validate_workflow_text(_workflow(uses=reference)), ())

    def test_rejects_mutable_short_and_dynamic_third_party_actions(self):
        references = (
            "actions/checkout@v4",
            "actions/checkout@main",
            "actions/checkout@abc1234",
            "${{ matrix.action }}",
            "docker://debian:12",
            "./../outside-action",
            "./local action",
        )
        for reference in references:
            with self.subTest(reference=reference):
                self.assertTrue(validate_workflow_text(_workflow(uses=reference)))

    def test_accepts_digest_pinned_container_service_and_image_fields(self):
        workflow = _workflow(container=f"debian:12@sha256:{DIGEST}") + f"""
  service-check:
    runs-on: ubuntu-24.04
    services:
      database:
        image: postgres:17@sha256:{DIGEST}
    steps:
      - uses: ./local-action
"""
        self.assertEqual(validate_workflow_text(workflow), ())

    def test_rejects_mutable_or_dynamic_container_service_and_image_fields(self):
        workflows = (
            _workflow(container="debian:12"),
            _workflow(container="${{ matrix.image }}"),
            _workflow().replace(
                "    steps:\n",
                "    container:\n    steps:\n",
                1,
            )
            + f"    image: unrelated:1@sha256:{DIGEST}\n",
            _workflow() + "    services: {database: {image: postgres:17}}\n",
            _workflow() + "    image: postgres:17\n",
            _workflow() + "    image: ${{ vars.SERVICE_IMAGE }}\n",
        )
        for workflow in workflows:
            with self.subTest(workflow=workflow):
                self.assertTrue(validate_workflow_text(workflow))

    def test_rejects_unpinned_wrong_or_overridden_checkout(self):
        mutations = (
            MINIMAL_POLICY.replace(PINNED_CHECKOUT, "actions/checkout@v4", 1),
            MINIMAL_POLICY.replace(PINNED_CHECKOUT, f"actions/checkout@{'a' * 40}", 1),
            MINIMAL_POLICY.replace(
                f"      - uses: {PINNED_CHECKOUT} # v4.4.0\n",
                f"      - uses: {PINNED_CHECKOUT} # v4.4.0\n        with:\n          ref: main\n",
                1,
            ),
            MINIMAL_POLICY.replace(
                f"      - uses: {PINNED_CHECKOUT} # v4.4.0\n",
                f"      - uses: {PINNED_CHECKOUT} # v4.4.0\n"
                f"      - uses: owner/other-action@{'c' * 40}\n",
                1,
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_policy_rejected(mutation)

    def test_rejects_top_level_job_and_step_execution_context_overrides(self):
        mutations = (
            MINIMAL_POLICY.replace("permissions:\n", "defaults:\n  run:\n    shell: bash\npermissions:\n", 1),
            MINIMAL_POLICY.replace("permissions:\n", "env:\n  PATH: .ci-shadow\npermissions:\n", 1),
            MINIMAL_POLICY.replace("    runs-on:", "    defaults:\n      run:\n        working-directory: .ci-shadow\n    runs-on:", 1),
            MINIMAL_POLICY.replace("    runs-on:", "    env:\n      PATH: .ci-shadow\n    runs-on:", 1),
            MINIMAL_POLICY.replace("    runs-on:", "    if: always()\n    runs-on:", 1),
            MINIMAL_POLICY.replace("    runs-on:", "    continue-on-error: true\n    runs-on:", 1),
            MINIMAL_POLICY.replace("    runs-on:", f"    container: debian@sha256:{DIGEST}\n    runs-on:", 1),
            MINIMAL_POLICY.replace("      - run:", "      - env:\n          PATH: .ci-shadow\n        run:", 1),
            MINIMAL_POLICY.replace("      - run:", "      - if: always()\n        run:", 1),
            MINIMAL_POLICY.replace("      - run:", "      - continue-on-error: true\n        run:", 1),
            MINIMAL_POLICY.replace("      - run:", "      - shell: bash\n        run:", 1),
            MINIMAL_POLICY.replace("      - run:", "      - working-directory: .ci-shadow\n        run:", 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_policy_rejected(mutation)

    def test_rejects_trigger_branch_permission_and_prt_drift(self):
        mutations = (
            MINIMAL_POLICY.replace("  pull_request:\n", "", 1),
            MINIMAL_POLICY.replace("  push:\n    branches: [main]\n", "", 1),
            MINIMAL_POLICY.replace("  workflow_dispatch:\n", "", 1),
            MINIMAL_POLICY.replace("    branches: [main]\n", "", 1),
            MINIMAL_POLICY.replace("    branches: [main]\n", "    branches: [develop]\n", 1),
            MINIMAL_POLICY.replace("permissions:\n  contents: read\n\n", "", 1),
            MINIMAL_POLICY.replace("  contents: read\n", "  contents: write\n", 1),
            MINIMAL_POLICY.replace("  pull_request:\n", "  pull_request:\n  pull_request_target:\n", 1),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_policy_rejected(mutation)

    def test_rejects_unsupported_key_and_flow_mapping_bypasses(self):
        workflows = (
            '? uses\n: actions/checkout@v4\n',
            '"u\\u0073es": actions/checkout@v4\n',
            "&key uses: actions/checkout@v4\n",
            "jobs: {check: {steps: [{uses: actions/checkout@v4}]}}\n",
            "steps: [uses: actions/checkout@v4]\n",
        )
        for workflow in workflows:
            with self.subTest(workflow=workflow):
                self.assertTrue(validate_workflow_text(workflow))

    def test_policy_has_no_native_evidence_dependency_or_external_trust_claim(self):
        checker = Path("tools/check_ci_supply_chain.py").read_text(encoding="utf-8")
        combined = MINIMAL_POLICY + checker
        for absent in ("native-core-evidence", "package-wheel", "desktop-core", "linux-container-core"):
            self.assertNotIn(absent, combined)

    def test_current_tracked_repository_passes(self):
        repository_root = Path(__file__).resolve().parents[2]
        self.assertEqual(validate_repository(repository_root), ())


if __name__ == "__main__":
    unittest.main()
