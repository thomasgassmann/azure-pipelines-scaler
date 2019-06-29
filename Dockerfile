FROM python:3.6-stretch
COPY . /app
WORKDIR /app
RUN pip install pipenv && pipenv install --system --deploy
CMD ["python", "-u", "-m", "aps"]
