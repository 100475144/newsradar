
FROM python:3.13

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1

#CMD ["fastapi", "dev", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/code/app"]