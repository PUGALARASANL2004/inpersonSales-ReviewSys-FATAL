# 1️⃣ Use stable Python base image
FROM python:3.10-bullseye

# 2️⃣ Set working directory
WORKDIR /app

# 3️⃣ Install system dependencies (audio + ffmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 4️⃣ Copy requirements first (better caching)
COPY requirements.txt .

# 5️⃣ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6️⃣ Copy application code
COPY api ./api
COPY examples ./examples
COPY scripts ./scripts

# 7️⃣ Expose FastAPI port
EXPOSE 8000

# 8️⃣ Start FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
