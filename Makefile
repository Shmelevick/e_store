run:
	uv run uvicorn app.main:app --port 8000 --reload
test:
	uv run pytest -v