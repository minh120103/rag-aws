FROM python:3.12-slim

ENV PYTHONPATH=/code

WORKDIR /code

EXPOSE 8000
#Expose port 8000 for local development, port 80 for deploying on AWS EC2

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir -r /code/requirements.txt

COPY ./app /code/app
COPY ./data /code/data
COPY ./isrgrootx1.pem /code/isrgrootx1.pem

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]