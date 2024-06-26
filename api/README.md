# FastAPI server

[based on fast api railway starter template](https://github.com/railwayapp-templates/fastapi/)

## 🥞Stack

- FastAPI
- [Hypercorn](https://hypercorn.readthedocs.io/)

## 👩‍💻 Running Locally

- `cd` into the `api/` dir
- create & start virtual environment `python3 -m venv .venv; source .venv/bin/activate`
- Install packages with pip using `pip install -r requirements.txt`
- Create `.env` file and add `OPENAI_API_KEY`
- Run locally using `hypercorn main:app --reload`
