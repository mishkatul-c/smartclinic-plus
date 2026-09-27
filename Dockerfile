FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV SMARTCLINIC_DATABASE=/data/smartclinic.db
RUN mkdir -p /data && python -m smartclinic.seed
EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "run:app", "run", "--host=0.0.0.0"]
