# shelly-plug-s-prometheus-exporter

```bash
$ docker run \
    -d \
    --name shelly-plug-s-prometheus-exporter \
    -p 9100:9100 \
    -e SHELLY_ENDPOINTS="http://192.168.178.111 http://192.168.178.112" \
    jblawatt/shelly-plug-s-prometheus-exporter:latest
```
