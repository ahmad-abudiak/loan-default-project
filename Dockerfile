FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY src/ src/
COPY api/ api/
COPY models/lightgbm_v2_calibrated.joblib models/typical_applicant.parquet models/demo_loans.parquet models/
COPY results/policy.json results/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]