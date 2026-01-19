conda deactivate
python3 -m venv venv
source venv/bin/activate

uvicorn --app-dir .. backend.app:app --host 127.0.0.1 --port 3000 --reload 