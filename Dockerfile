FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY app.py ./
COPY src ./src
COPY assets ./assets
COPY static ./static
COPY locales ./locales
COPY data ./data
COPY sources ./sources
COPY docs ./docs
COPY .streamlit/config.toml ./.streamlit/config.toml
RUN chown -R appuser:appuser /app/data
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.runOnSave=false"]
