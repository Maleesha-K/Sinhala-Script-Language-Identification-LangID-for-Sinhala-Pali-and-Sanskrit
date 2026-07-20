# LangID Web Application MVP

This directory contains the Minimum Viable Product (MVP) web application for the Sinhala-Script Language Identification (LangID) system, designed as a two-tier application using **FastAPI** (Backend) and **Streamlit** (Frontend).

## Prerequisites

Before running the application, ensure you have trained and exported the models by running:
```bash
python scripts/export_3way_model.py
```
This will create `langid_vectorizer.pkl` and `langid_model.pkl` in the `models/` directory.

Ensure you have the required dependencies installed (they should already be available if you used the provided `requirements.txt`):
```bash
pip install fastapi uvicorn streamlit pydantic joblib
```

## Running the Application Locally

The application runs in two parts: the backend API and the frontend UI. You will need to open **two separate terminal windows**.

### 1. Start the FastAPI Backend
Open the first terminal, navigate to the root of the project, and run:
```bash
uvicorn webapp.backend.main:app --reload --port 8000
```
- The backend will start on `http://localhost:8000`
- You can view the interactive API documentation at `http://localhost:8000/docs`

### 2. Start the Streamlit Frontend
Open the second terminal, navigate to the root of the project, and run:
```bash
streamlit run webapp/frontend/app.py
```
- The frontend will open automatically in your browser at `http://localhost:8501`

## Features
- **Dynamic Processing**: Evaluates complete sentences or single words accurately using character n-grams.
- **Color-Coded Rendering**: High-contrast, pastel background highlights visually represent the predicted language (Sinhala = Light Blue, Pali = Light Green, Sanskrit = Light Yellow).
- **Graceful Error Handling**: Fallbacks seamlessly if the backend is down or the input is unsupported.
