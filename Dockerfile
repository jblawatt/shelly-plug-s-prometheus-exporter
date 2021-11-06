FROM python:3.9-slim-bullseye

ENV PORT=9100
ENV SHELLY_ENDPOITNS=

EXPOSE $PORT

RUN pip install requests prometheus-client

ADD exporter.py /exporter.py

CMD ["python", "exporter.py"]
