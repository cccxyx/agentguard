FROM dockerproxy.net/library/python:3.11-slim

WORKDIR /app

ENV PIP_INDEX_URL=https://repo.huaweicloud.com/repository/pypi/simple
ENV PIP_TRUSTED_HOST=repo.huaweicloud.com

COPY deploy/mcp_server/requirements.txt /tmp/mcp-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/mcp-requirements.txt

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY config ./config
COPY deploy ./deploy

RUN pip install --no-cache-dir --no-deps .

EXPOSE 8080

CMD ["uvicorn", "deploy.mcp_server.server:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
