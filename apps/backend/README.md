# Repair DIY AI Backend

Backend API for the Repair DIY AI application built with FastAPI, Pydantic, OpenAI, and pandas.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment file and configure:
```bash
cp env.example .env
# Edit .env with your OpenAI API key
```

4. Run the development server:
```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Dependencies

- FastAPI: Web framework
- Pydantic: Data validation
- OpenAI: AI integration
- pandas: Data manipulation
- uvicorn: ASGI server
