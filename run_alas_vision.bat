@echo off
echo Starting ALAS with Vision OCR...
if "%GOOGLE_API_KEY%"=="" (
    echo WARNING: GOOGLE_API_KEY not set! Vision OCR will fall back to traditional OCR.
    echo To set it: set GOOGLE_API_KEY=your-actual-api-key
)
poetry run python alas.py