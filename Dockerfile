FROM python:3.12-slim
WORKDIR /service
COPY requirements.txt requirements-semantic.txt ./
ARG INCLUDE_SEMANTIC=0
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INCLUDE_SEMANTIC" = "1" ]; then pip install --no-cache-dir -r requirements-semantic.txt; fi
COPY app ./app
COPY scripts ./scripts
RUN useradd -r -u 10001 appuser && mkdir -p /data && chown appuser:appuser /data
USER appuser
ENV AIHAS_DB=/data/aihas.db
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--proxy-headers"]
