from __future__ import annotations

from typing import Any

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def correlate_alerts(
    anomalies: list[dict[str, Any]], *, window_sec: int = 60
) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for anomaly in sorted(anomalies, key=lambda item: float(item["timestamp"])):
        for cluster in clusters:
            if abs(float(anomaly["timestamp"]) - float(cluster["last_ts"])) <= window_sec:
                cluster["anomalies"].append(anomaly)
                cluster["last_ts"] = max(float(cluster["last_ts"]), float(anomaly["timestamp"]))
                cluster["root_anomaly"] = _root(cluster["anomalies"])
                cluster["label"] = f"{cluster['root_anomaly']['type']} incident"
                break
        else:
            clusters.append(
                {
                    "label": f"{anomaly['type']} incident",
                    "root_anomaly": anomaly,
                    "anomalies": [anomaly],
                    "last_ts": anomaly["timestamp"],
                }
            )
    return clusters


def _root(anomalies: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        anomalies,
        key=lambda item: (
            -SEVERITY_RANK.get(str(item.get("severity", "low")), 0),
            float(item["timestamp"]),
        ),
    )[0]
