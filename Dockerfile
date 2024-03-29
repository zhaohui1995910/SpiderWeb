FROM python:3.7

WORKDIR /spider-web

COPY requirements.txt .

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8888

CMD gunicorn -c gunicorn.py main:app