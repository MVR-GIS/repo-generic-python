# Runbook — Running tests (repo-generic-python)

## Purpose

Run and troubleshoot the automated test suite for this repository.

The goals are to:

- validate that core tooling (including `tools/foundry_threads.py`) works as expected
- detect regressions early when the template evolves
- provide a repeatable workflow that works on Windows (USACE GFE) and offline environments

---

## Preconditions

You should have:

- a local clone of a repo created from the template `MVR-GIS/repo-generic-python`
- Miniforge installed (conda-forge) and `mamba` available
- a terminal:
  - Windows PowerShell, or
  - Miniforge Prompt

---

## Step 1 — Create (or update) the conda environment

Open a terminal and `cd` to the repository root (the folder containing `environment.yml`).

### 1.1 Create the environment (first time)

    mamba env create -f environment.yml

### 1.2 Activate the environment

    conda activate analysis

### 1.3 Update the environment (if it already exists)

If `environment.yml` has changed (for example, `pytest` was added), run:

    mamba env update -f environment.yml --prune
    conda activate analysis

### 1.4 Quick verification

    python --version
    pytest --version

If `pytest --version` fails, confirm `pytest` is listed in `environment.yml`, then re-run Step 1.3.

---

## Step 2 — Confirm the test files exist

From the repo root, confirm these paths exist:

- `tools/foundry_threads.py`
- `tests/test_foundry_threads.py`
- `tests/fixtures/threads_export.json`

Example checks (PowerShell):

    dir tools
    dir tests
    dir tests\fixtures

---

## Step 3 — Run the full test suite

From the repo root:

    pytest

Expected result:

- exit code 0 (success)
- output shows tests passing (example: `2 passed`)

---

## Step 4 — Run targeted tests

### 4.1 Run tests for Foundry Threads tooling only

    pytest -k foundry_threads

### 4.2 Run a specific test file

    pytest tests/test_foundry_threads.py

---

## Step 5 — Troubleshooting

### 5.1 `ModuleNotFoundError: No module named 'tools'`

**Cause:** You are not running `pytest` from the repository root.

**Fix:**

- `cd` to the repo root (where `environment.yml` lives)
- rerun:

    pytest

### 5.2 `pytest` is not recognized / command not found

**Cause:** The `analysis` environment is not active or does not include `pytest`.

**Fix:**

    conda activate analysis
    pytest --version

If `pytest` is still missing:

    mamba env update -f environment.yml --prune
    conda activate analysis
    pytest --version

### 5.3 Test fails because the expected output file name is different (date mismatch)

**Cause:** The test fixture `tests/fixtures/threads_export.json` controls the expected
output date via `metadata.createdAt`. If that fixture changes, the expected file name
may also change.

**Fix options:**

- update `tests/fixtures/threads_export.json` so `createdAt` matches the expected date, or
- update the test expectation to match the fixture.

### 5.4 YAML front matter parsing fails

**Cause:** The transcript output may no longer start with a YAML front matter block (`---`).

**Fix:**

- ensure the transcript renderer still writes YAML front matter at the top of the file, or
- if the format was intentionally changed, update the helper that parses front matter in the tests.

---

## Step 6 — Clean re-run (if things get weird)

If your environment is corrupted or you want to validate from scratch:

    conda deactivate
    conda env remove -n analysis
    mamba env create -f environment.yml
    conda activate analysis
    pytest

---

## Definition of done

You are done when:

- `pytest` passes locally when run from the repo root
- tests validate:
  - transcript markdown is written with YAML front matter
  - raw export JSON is written under `dev/sessions/.raw/`
  - backups are created under `dev/sessions/.backups/` on overwrite