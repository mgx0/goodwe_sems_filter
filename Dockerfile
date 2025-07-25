FROM python:3.12-slim

# Install dependencies
WORKDIR /app
COPY requirements.txt /app
RUN apt-get update && apt-get install bash
RUN pip install --no-cache-dir -r requirements.txt

ENV ENABLE_DOWNLOAD=False
ENV DEBUG=False
ENV GOODWE_TCP_SERVER=tcp.goodwe-power.com

# Copy application
COPY goodwe_sems_filter.py /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run the server
ENTRYPOINT /entrypoint.sh
