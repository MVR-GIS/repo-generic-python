# repo-generic-python

A template repository for lightweight Python data science analysis projects.

This template is designed for:
- Windows (USACE GFE)
- VS Code
- Miniforge (conda-forge) + mamba
- one environment per repository, defined by `environment.yml`
- notebooks as a first-class analysis workflow

---

## Table of Contents

1. Prerequisites
2. Create a new repository from this template
3. Clone your new repository
4. Create the conda environment
5. Open the project in VS Code
6. Configure VS Code to use the environment
7. Daily workflow
8. Project structure
9. Managing the environment

---

## 1. Prerequisites

### 1.1 Git
Verify Git is installed:

    git --version

If Git is not installed, install it using your organization’s approved method.

### 1.2 Miniforge + mamba
Conda manages Python and project dependencies. Miniforge is a minimal, conda-forge–oriented installer that supports per-user installs on Windows.

1. Download the Miniforge installer:
   https://github.com/conda-forge/miniforge/releases

2. Run the installer (Windows: `.exe`).

3. Close and reopen your terminal, then verify:

    conda --version
    mamba --version

If `mamba` is not available, install it into `base`:

    conda install -n base mamba -c conda-forge
    mamba --version

### 1.3 Visual Studio Code
Install VS Code using your organization’s approved method.

Recommended extensions:
- Python (Microsoft)
- Jupyter (Microsoft)

---

## 2. Create a new repository from this template

1. In GitHub, open this template repository: `MVR-GIS/repo-generic-python`.
2. Click **Use this template**.
3. Create your new repository:
   - Owner: `MVR-GIS` (or your approved org/user location)
   - Repository name: choose a descriptive name (example: `my-analysis-project`)
   - Visibility: choose per project needs (public or private)
4. After GitHub creates your new repository, copy its clone URL (HTTPS).

---

## 3. Clone your new repository

1. Open a terminal (or Miniforge Prompt on Windows if conda is not on your system PATH).
2. Navigate to where you store projects:

    cd ~/Documents

3. Clone your new repository (replace with your repo name):

    git clone https://github.com/MVR-GIS/<YOUR-NEW-REPO>.git

4. Move into the project directory:

    cd <YOUR-NEW-REPO>

---

## 4. Create the conda environment

The `environment.yml` file defines the project environment. This template standardizes the environment name as `analysis`.

### 4.1 Create the environment

From the repo root:

    mamba env create -f environment.yml

### 4.2 Activate the environment

    conda activate analysis

Verify Python runs:

    python --version

---

## 5. Open the project in VS Code

From the repo root:

    code .

---

## 6. Configure VS Code to use the environment

1. Open the Command Palette (Ctrl+Shift+P).
2. Run: Python: Select Interpreter
3. Choose the interpreter for the `analysis` conda environment.

---

## 7. Daily workflow

1. Pull the latest changes:

    git pull

2. Activate the environment:

    conda activate analysis

3. Open VS Code:

    code .

If `environment.yml` changed, update your environment:

    mamba env update -f environment.yml --prune

---

## 8. Project structure

- `notebooks/` — Jupyter notebooks (analysis + narrative)
- `src/` — reusable Python code (helpers, functions, modules)
- `data/` — data (follow your project’s data policy)
- `outputs/` — figures/tables/results produced by analysis

---

## 9. Managing the environment

### Add a new package
1. Add the package to `environment.yml` under `dependencies`.
2. Update your local environment:

    mamba env update -f environment.yml --prune

3. Commit the updated `environment.yml`.

### Deactivate the environment

    conda deactivate

### Remove and recreate the environment (if needed)

    conda deactivate
    conda env remove -n analysis
    mamba env create -f environment.yml
    conda activate analysis

### Export an exact environment snapshot (optional)

    conda env export > environment-lock.yml
