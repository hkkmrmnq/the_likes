FROM python:3.12

WORKDIR /app

RUN apt-get update && apt-get install -y supervisor && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/log/supervisor

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN UV_DEV=False uv sync --frozen

COPY . .

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
