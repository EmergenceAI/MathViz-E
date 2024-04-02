FROM python:3.11
COPY *.* /
COPY src /src
COPY src/.env /src/.env
COPY src/static/* /src/static/*
WORKDIR /
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5001
CMD ["python", "-m", "src.main"]
