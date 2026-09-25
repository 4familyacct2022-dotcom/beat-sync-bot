FROM python:3.10-slim

# Install system dependencies for MoviePy & FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    git \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow video/text rendering
RUN sed -i 's/domain="coder" rights="none" pattern="LABEL"/domain="coder" rights="read|write" pattern="LABEL"/' /etc/ImageMagick-6/policy.xml

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Run the bot
CMD ["python", "bot.py"]
