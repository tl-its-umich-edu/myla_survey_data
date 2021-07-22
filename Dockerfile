FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-c", "guniconf.py", "myla_survey.wsgi"]