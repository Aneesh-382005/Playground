# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
# PYTHONDONTWRITEBYTECODE: Stops Python creating .pyc files (cleaner container, faster startup)
# PYTHONUNBUFFERED: Forces logs to appear immediately (critical for debugging in Docker)
# PIP_NO_CACHE_DIR: Reduces image size by not caching pip downloads
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by Manim
# BUILD TOOLS (needed to compile pycairo from source):
#   - build-essential: gcc, g++, make (needed for pip to build pycairo)
#   - pkg-config: helps find Cairo libraries during compilation
#   - libcairo2-dev: Cairo headers for pycairo compilation
# RUNTIME DEPENDENCIES:
#   - ffmpeg: Video rendering (Manim core requirement)
#   - texlive-latex-*: LaTeX rendering (lighter than texlive-full, saves ~4GB)
#   - poppler-utils: SVG/PDF utilities
#   - libcairo2/libpango: Required by Manim for text/shape rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libcairo2-dev \
    ffmpeg \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-latex-recommended \
    poppler-utils \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the renderer's source code into the container
COPY . .

# Expose port 8000 for FastAPI (if running web service)
EXPOSE 8000

# Default command to run FastAPI app (comment out if not using FastAPI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
