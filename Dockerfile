FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV COLLABCANVAS_PUBLIC=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080
CMD ["sh","-c","python3 server.py --port ${PORT:-8080} --state runtime/public-state.json"]
