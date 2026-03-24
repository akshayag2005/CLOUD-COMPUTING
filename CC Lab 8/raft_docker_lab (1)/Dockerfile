FROM python:3.7.16-bullseye

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/zhebrak/raftos.git
WORKDIR /opt/raftos
RUN sed -i 's/cryptography==1.5.3/cryptography==3.3.2/' requirements.txt
RUN pip install --no-cache-dir .

WORKDIR /app
COPY node.py .

CMD ["python","node.py"]
