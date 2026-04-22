# repo-generic-python

A template repository for data science Python analysis projects. Follow the setup instructions below to get your local environment ready for work.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Create the Conda Environment](#3-create-the-conda-environment)
4. [Open the Project in VS Code](#4-open-the-project-in-vs-code)
5. [Configure VS Code to Use the Environment](#5-configure-vs-code-to-use-the-environment)
6. [Daily Workflow](#6-daily-workflow)
7. [Project Structure](#7-project-structure)
8. [Managing the Environment](#8-managing-the-environment)

---

## 1. Prerequisites

### 1.1 Install Git

If Git is not already installed, download and install it from <https://git-scm.com/downloads>. Accept all defaults during installation.

Verify the installation by opening a terminal (Command Prompt, PowerShell, or macOS/Linux Terminal) and running:

```bash
git --version
```

### 1.2 Install Miniforge + mamba

Conda is the tool used to manage Python and all project dependencies. Miniconda is a minimal installer for conda.

1. Download the **Miniforge** installer for your operating system from:  
   <https://github.com/conda-forge/miniforge/releases>

2. Run the installer and follow the prompts:
   - **Windows**: Run the `.exe` installer. 

3. Close and reopen your terminal, then verify the installation:
   ```bash
   mamba --version
   ```

### 1.3 Install Visual Studio Code

1. Download VS Code from <https://code.visualstudio.com/>.
2. Run the installer and accept all defaults.

---

## 2. Clone the Repository

You must be a member of the GitHub Organization to access this repository.

1. Open a terminal (or **Miniforge Prompt** on Windows if conda is not on your system PATH).

2. Navigate to the folder where you want to store the project:
   ```bash
   cd ~/Documents   # or any preferred location
   ```

3. Clone the repository:
   ```bash
   git clone https://github.com/<your-org>/repo-generic-python.git
   ```
   Replace `<your-org>` with the actual GitHub Organization name.

4. Move into the project directory:
   ```bash
   cd repo-generic-python
   ```

---

## 3. Create the Conda Environment

The `environment.yml` file at the root of the project defines the shared Python environment (packages and their versions). Everyone on the team uses this same file to create an identical, reproducible environment.

### 3.1 Create the environment

Run the following command from inside the `repo-generic-python` directory:

```bash
mamba env create -f environment.yml
```

This command reads `environment.yml`, downloads the required packages, and creates a mamba environment named **`analysis`**.

> **Note:** This step only needs to be performed once per machine. Creating the environment may take several minutes depending on your internet connection.

### 3.2 Activate the environment

```bash
conda activate analysis
```

Your terminal prompt will update to show `(analysis)` at the beginning, confirming the environment is active.

---

## 4. Open the Project in VS Code

From your terminal (with the conda environment activated), open VS Code in the project directory:

```bash
code .
```

VS Code will open with the `repo-generic-python` folder as your workspace.

### 4.1 Install Recommended Extensions

VS Code will display a notification asking if you want to install the **recommended extensions** for this workspace. Click **"Install All"**.

If the prompt does not appear automatically, open the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`), click the **filter icon (⋯)**, and select **"Show Recommended Extensions"**, then install all of them.

The recommended extensions include:

| Extension | Purpose |
|---|---|
| Python | Core Python language support |
| Jupyter | Run and edit Jupyter notebooks in VS Code |

---

## 5. Configure VS Code to Use the Environment

VS Code needs to know which Python interpreter to use.

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
2. Type **"Python: Select Interpreter"** and press `Enter`.
3. From the list, choose the interpreter that shows **`analysis`** — it will look like:
   ```
   Python 3.11.x ('analysis': conda)
   ```

After selecting the interpreter, all Python files and Jupyter notebooks in the workspace will use the `analysis` conda environment automatically.

---

## 6. Daily Workflow

Each time you begin working on the project:

1. **Pull the latest changes** from the remote repository:
   ```bash
   git pull
   ```

2. **Check if the environment needs updating** (if `environment.yml` changed):
   ```bash
   conda env update -f environment.yml --prune
   ```
   The `--prune` flag removes packages that were removed from `environment.yml`.

3. **Activate the environment** (if not already active in your terminal):
   ```bash
   conda activate analysis
   ```

4. **Open VS Code**:
   ```bash
   code .
   ```

5. Work on your analysis in the `notebooks/` directory or add reusable code to `src/`.

6. **Commit and push your work**:
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   git push
   ```

---

## 7. Project Structure

```
repo-generic-python/
├── .vscode/
│   ├── extensions.json   # Recommended VS Code extensions
│   └── settings.json     # Workspace Python/Jupyter settings
├── data/                 # Raw and processed data files (not committed by default)
├── notebooks/            # Jupyter notebooks for analysis
├── outputs/              # Charts, tables, and other outputs
├── src/                  # Reusable Python modules and helper functions
│   └── __init__.py
├── .gitignore            # Files and folders excluded from git
├── environment.yml       # Conda environment specification
├── LICENSE
└── README.md
```

> **`data/` and `outputs/`** directories are included in the repo structure but their contents are excluded from git by default. Add large or sensitive files to `.gitignore` as needed.

---

## 8. Managing the Environment

### Add a new package

1. Add the package to `environment.yml` under `dependencies`.
2. Update your local environment:
   ```bash
   conda env update -f environment.yml --prune
   ```
3. Commit the updated `environment.yml` so teammates can sync:
   ```bash
   git add environment.yml
   git commit -m "Add <package-name> to project environment"
   git push
   ```

### Deactivate the environment

```bash
conda deactivate
```

### Remove and recreate the environment (if needed)

```bash
conda deactivate
conda env remove -n project-env
conda env create -f environment.yml
```

### Export an exact environment snapshot

To capture the exact versions of every installed package (useful for archiving a finished project):

```bash
conda env export > environment-lock.yml
```