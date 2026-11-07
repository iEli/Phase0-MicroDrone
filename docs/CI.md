# Module continuous integration

The workflows in [`.github/workflows/`](../.github/workflows/) test the existing
synthetic Python modules. Each workflow runs on Ubuntu 24.04 with Python 3.12
and 3.14. Relevant pull requests and pushes to `main` trigger the checks;
`workflow_dispatch` also permits manual runs once the workflow is on the default
branch. A feature-branch push alone does not trigger a run.

| Workflow | Existing coverage |
| --- | --- |
| CV CI | CV observation interface, perception, and benchmark tests |
| Motion CI | All tests under `motion_engine/tests`, including failure injection and trace checks |
| State Machine CI | Mission transitions, demos, and Motion/state-machine alignment |
| Safety CI | Policy, legacy decisions, concrete command checks, and the Motion adapter |
| Universal Log CI | Shared logger output, serialization, and Motion/CV logging interoperability |
| Docking CI | Alignment, phases, replay, hazard cancellation, and Safety policy/command checks |

Navigation and Simulation currently contain documentation and placeholders, with
no runnable module tests. Hardware and Electronics also have no Python test
suites. Add CI jobs for those modules when they have a meaningful runnable check.
These workflows do not install PX4, ROS, Gazebo, or external submodules, and do
not change mission behavior or deploy anything.

## Dependencies and local reproduction

All workflows use pytest to run their existing pytest/unittest suites and emit
JUnit XML reports. Each job installs
[requirements-ci.txt](../requirements-ci.txt); CV additionally installs its
existing [requirements](../cv/requirements.txt). Separate jobs prevent CV
dependencies from being required for other modules. Run commands from the
repository root in an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-ci.txt -r cv/requirements.txt

# CV
python -B -m pytest tests/test_computer_vision.py -v
python -B -m pytest tests/test_cv*.py -v

# Motion
python -B -m pytest motion_engine/tests -v

# State Machine
python -B -m pytest state_machine/tests motion_engine/tests/test_state_machine_alignment.py -v

# Safety
python -B -m pytest tests/test_safety*.py -v
python -B -m pytest tests/test_command_check.py -v
python -B -m pytest motion_engine/tests/test_safety_adapter.py -v

# Universal Log
python -B -m pytest motion_engine/tests/test_universal_logging.py -v

# Docking (includes its Safety dependencies)
python -B -m pytest tests/test_docking*.py -v
python -B -m pytest tests/test_command_check.py -v
python -B -m pytest tests/test_safety_policy.py -v
```

## Viewing results

Open the repository's **Actions** tab and choose a module workflow. Each run
contains separate Python-version jobs and named test steps. Pull requests also
show the runs under **Checks**. A failure reports the test and traceback;
subsequent test steps still run unless the workflow was cancelled.

Path filters include each module's imported local dependencies, its test files,
and workflow/configuration changes. If an import dependency moves, update the
filters too. These are scoped checks: unrelated changes can skip a workflow.
Do not mark a path-filtered workflow as a universally required branch-protection
check without accounting for skipped runs. No branch protection is configured
by this change.

## Downloadable test reports

Every test step writes a separate JUnit XML file under `test-results/`. Reports
include test names, durations, and failure/error tracebacks. Pytest runs existing
unittest cases as well as pytest tests; the test files selected by CI are unchanged.
Docking's tests still use only standard-library/local modules, but its CI job now
installs pytest as the reporting runner.

An artifact upload runs after the test steps even when a step fails. It does not
change test exit codes: failing tests still fail the job. Each module/Python
version/run attempt has its own artifact name, avoiding collisions between matrix
jobs and reruns. Reports are retained for 14 days, subject to repository policy.

In GitHub, open **Actions → module workflow → run**, then download the ZIP under
**Artifacts**. Extract it to view the XML locally or import it into a JUnit-aware
tool. This change provides downloadable files; individual results and tracebacks
also remain available in the test-step logs.

If setup fails before tests run, or a job is cancelled before reports are written,
there may be no XML to upload. The upload step warns about missing files instead
of hiding the original failure. Job-level cancellation/timeouts can prevent an
upload from completing.

To reproduce reporting locally, append a unique output path to each command:

```bash
python -B -m pytest tests/test_docking*.py -v --junitxml=test-results/docking.xml
```

Generated reports and pytest caches are ignored by Git. The upload step includes
only `test-results/*.xml`, not arbitrary files from the workspace.
