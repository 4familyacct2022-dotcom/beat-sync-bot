FROM python:3.10-slim

# Install system dependencies for MoviePy & FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    git \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow video/text rendering (works for both v6 and v7 layouts)
RUN policy_file=$(find /etc/ImageMagick-6 /etc/ImageMagick-7 -name policy.xml 2>/dev/null | head -n 1) && \
    if [ -n "$policy_file" ]; then \
      sed -i 's/domain="coder" rights="none" pattern="LABEL"/domain="coder" rights="read|write" pattern="LABEL"/' "$policy_file"; \
    fi

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Run the bot
CMD ["python", "bot.py"]
