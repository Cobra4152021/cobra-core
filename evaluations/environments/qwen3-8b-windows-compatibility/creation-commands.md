# Creation commands — Python 3.12 isolated environment

Executed on the Phase 3D host. Primary `.venv` is never activated for these steps.

```powershell
# Interpreter (side-by-side; does not replace Python 3.13)
py -3.12 -c "import sys; print(sys.executable, sys.version)"

# Create venv without system site packages
py -3.12 -m venv .venv-qwen312 --without-pip
.\.venv-qwen312\Scripts\python.exe -m ensurepip --upgrade
.\.venv-qwen312\Scripts\python.exe -m pip install --upgrade pip==25.0.1 setuptools==78.1.0 wheel==0.45.1

# CUDA 12.4 torch wheel
.\.venv-qwen312\Scripts\python.exe -m pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124

# Remaining exact pins
.\.venv-qwen312\Scripts\python.exe -m pip install -r evaluations/environments/qwen3-8b-windows-compatibility/requirements-qwen312-lock.txt

# Freeze
.\.venv-qwen312\Scripts\python.exe -m pip freeze > evaluations/environments/qwen3-8b-windows-compatibility/python312/pip-freeze.txt
.\.venv-qwen312\Scripts\python.exe -m pip check
```

Python 3.11 environment is **not** created unless Python 3.12 fails qualification gates.
