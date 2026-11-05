# 🐛 This Dockerfile "works" but has at least 6 problems a reviewer would flag. Fix them (see README).
FROM python:3.13

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "lessons.r4_deployment.exercise.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
