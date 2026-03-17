# Как запускать
## Windows (cmd)
```cmd
python -m venv .venv
.venv/scripts/activate
pip install -r requirements.txt
playwright install chromium
python -m src.main
```
## Linux (bash)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python -m src.main
```
