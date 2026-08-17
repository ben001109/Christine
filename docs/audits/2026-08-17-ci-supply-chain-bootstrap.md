# CI supply-chain policy bootstrap

This bootstrap consists only of the dedicated workflow
`.github/workflows/ci-supply-chain-policy.yml`, its dependency-free checker at
`tools/check_ci_supply_chain.py`, and focused standard-library tests. Once these
files are present on the remote default branch, the committed workflow can run
on pull requests, pushes to `main`, and manual dispatches.

The job deliberately omits a custom job name. Its expected default check context
is the stable job identifier `ci-supply-chain-policy`. The actual check context
reported on a GitHub pull request must be read and verified before merge.

GitHub rulesets, required workflows, branch protection, and required-check state
are external repository configuration. This bootstrap neither configures nor
verifies that state and does not claim that the checker is an external trust
boundary. Land the bootstrap first; a repository administrator can then verify
the observed check context and configure the trusted required workflow or check.
