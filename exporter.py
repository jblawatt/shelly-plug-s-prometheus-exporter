from prometheus_client import start_http_server, Metric, REGISTRY
import requests
import os
import time
import logging
from urllib.parse import urlparse

class ShellyMetricsCollector:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.url = urlparse(endpoint)

    def _collect_meter(self):
        response = requests.get(f"{self.endpoint}/meter/0")
        j = response.json()

        m = Metric("meter_0", "Meter 0", "summary")

        for key, value in j.items():
            if isinstance(value, (list, tuple)):
                continue
            m.add_sample(key, value=value, labels={"host": self.url.netloc})

        return m

    def collect(self):
        yield self._collect_meter()


class ShellyPlugSCollector:
    def __init__(
        self, endpoint, meter_metric, relay_metric, status_metric, settings_metric
    ):
        self.endpoint = endpoint
        self.url = urlparse(endpoint)
        self.meter_metric = meter_metric
        self.relay_metric = relay_metric
        self.settings_metric = settings_metric
        self.status_metric = status_metric

    def _collect_meter(self):
        data = requests.get(f"{self.endpoint}/meter/0").json()
        for key, value in data.items():
            if isinstance(value, (list, dict, tuple)):
                continue
            self.meter_metric.add_sample(
                key, value=value, labels={"host": self.url.netloc}
            )

    def _collect_relay(self):
        data = requests.get(f"{self.endpoint}/relay/0").json()
        for key, value in data.items():
            if isinstance(value, (list, dict, tuple, str)):
                continue
            self.relay_metric.add_sample(
                key, value=value, labels={"host": self.url.netloc}
            )

    def _collect_settings(self):
        pass

    def _collect_status(self):
        data = requests.get(f"{self.endpoint}/status").json()
        for i, relay in enumerate(data["relays"]):
            for key, value in relay.items():
                if isinstance(value, (list, dict, tuple, str)):
                    continue
                self.status_metric.add_sample(
                    f"relays_{i}_{key}", value=value, labels={"host": self.url.netloc}
                )
                self.status_metric.add_sample(
                    f"relays_{key}",
                    value=value,
                    labels={"index": str(i), "host": self.url.netloc},
                )

        for i, meter in enumerate(data["meters"]):
            for key, value in meter.items():
                if isinstance(value, (list, dict, tuple, str)):
                    continue
                self.status_metric.add_sample(
                    f"meter_{i}_{key}", value=value, labels={"host": self.url.netloc}
                )
                self.status_metric.add_sample(
                    f"meter_{key}",
                    value=value,
                    labels={"index": str(i), "host": self.url.netloc}
                )

        self.status_metric.add_sample(
            "temperature", value=data["temperature"], labels={"host": self.url.netloc}
        )
        self.status_metric.add_sample(
            "overtemperature",
            value=data["overtemperature"],
            labels={"host": self.url.netloc},
        )

        self.status_metric.add_sample(
            "ram_free",
            value=data["ram_free"],
            labels={"host": self.url.netloc},
        )

        self.status_metric.add_sample(
            "ram_total",
            value=data["ram_total"],
            labels={"host": self.url.netloc},
        )

        try:
            self.status_metric.add_sample(
                "tC", value=data["tmp"]["tF"], labels={"host": self.url.netloc}
            )
        except KeyError:
            pass

        try:
            self.status_metric.add_sample(
                "tF", value=data["tmp"]["tF"], labels={"host": self.url.netloc}
            )
        except KeyError:
            pass

    def collect(self):
        self._collect_meter()
        self._collect_relay()
        self._collect_settings()
        self._collect_status()


class GroupedmetricsCollector:
    def __init__(self, endpoints):
        self.endpoint = endpoints
        self.meter_metric = Metric("meter_0", "Meter 0", "summary")
        self.relay_metric = Metric("relay_0", "relay 0", "summary")
        self.status_metric = Metric("status", "Status", "summary")
        self.settings_metric = Metric("status", "Status", "summary")
        self.collectors = [
            ShellyPlugSCollector(
                endpoint,
                self.meter_metric,
                self.relay_metric,
                self.status_metric,
                self.settings_metric,
            )
            for endpoint in endpoints
        ]

    def run_collectors(self):
        for c in self.collectors:
            c.collect()

    def collect(self):
        self.run_collectors()
        yield from [
            self.meter_metric,
            self.relay_metric,
            self.status_metric,
            self.settings_metric,
        ]


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    port = os.getenv("PORT")
    endpoints = os.getenv("SHELLY_ENDPOINTS")
    endpoints = list(map(lambda s: s.strip().strip("/"), endpoints.split(" ")))

    start_http_server(int(port))
    REGISTRY.register(GroupedmetricsCollector(endpoints))

    while True:
        time.sleep(1)
