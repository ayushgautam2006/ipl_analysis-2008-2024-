FROM python:3.13-slim

WORKDIR /ipl_analysis

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-trained model artifacts from the root directory
COPY model.pkl .
COPY encoder.pkl .
COPY team_stats.json .

# Copy Flask app code
COPY app/ app/

EXPOSE 5000

CMD ["gunicorn", "--workers=2", "--bind=0.0.0.0:5000", "--timeout=120", "app.app:app"]
