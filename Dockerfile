FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_SECRET_KEY=$FLASK_SECRET_KEY

EXPOSE 5000

CMD ["python", "app.py"]
