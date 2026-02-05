FROM python:3.9-slim

# Install RabbitMQ client library
RUN pip install pika

# Set working directory
WORKDIR /app

# Copy application code
COPY chat.py .

# Create the data directory for chat history
RUN mkdir -p /app/data

# Run the chat application
CMD ["python", "-u", "chat.py"]
