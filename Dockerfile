FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y \
    git curl build-essential unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

WORKDIR /app

# Install Python deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create workspace dir
RUN mkdir -p workspace/default workspace/uploads

# Expose port
EXPOSE 8000

# Default: run both services
CMD ["uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
