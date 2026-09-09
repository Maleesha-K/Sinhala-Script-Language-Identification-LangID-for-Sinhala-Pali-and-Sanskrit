# LangID Web Application

This directory contains the web application for the Sinhala-Script Language Identification (LangID) system, designed as a two-tier application using **FastAPI** (Backend) and **Next.js** (Frontend).

## Prerequisites

Before running the application, ensure you have trained and exported the models by running:
```bash
python scripts/export_3way_model.py
```
This will create `langid_vectorizer.pkl` and `langid_model.pkl` in the `models/` directory.

Ensure you have the required dependencies installed for the backend:
```bash
pip install fastapi uvicorn pydantic joblib
```
For the frontend, ensure you have Node.js installed, then run:
```bash
cd webapp/frontend
npm install
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

### 2. Start the Next.js Frontend
Open the second terminal, navigate to the frontend directory, and run:
```bash
cd webapp/frontend
npm run dev
```
- The frontend will open automatically in your browser at `http://localhost:3000`

## Features
- **Dynamic Processing**: Evaluates complete sentences or single words accurately using character n-grams.
- **Color-Coded Rendering**: High-contrast, pastel background highlights visually represent the predicted language (Sinhala = Light Blue, Pali = Light Green, Sanskrit = Light Yellow).
- **Graceful Error Handling**: Fallbacks seamlessly if the backend is down or the input is unsupported.
