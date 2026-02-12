FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Expose the port Cloud Run expects
ENV PORT=8080
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
