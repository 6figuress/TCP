FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt update && apt install -y \
    curl \
    blender \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements files
COPY pyproject.toml .
COPY .python-version .

# Install dependencies using uv
RUN uv sync

# Copy the rest of the application
COPY . .

# Expose the port your API runs on
EXPOSE 5000

# Command to run the API
CMD ["uv", "run", "server.py"]
