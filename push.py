import psutil
from datetime import datetime, timezone
from elasticsearch import Elasticsearch

# Connect to Elasticsearch (adjust URL if needed)
es = Elasticsearch("http://localhost:9200")

def push_disk_usage(shares, index="disk-metrics"):
    for share in shares:
        try:
            usage = psutil.disk_usage(share)
            now = datetime.now(timezone.utc).isoformat()

            # Push multiple metrics as separate docs
            metrics = {
                "disk_total_gb": usage.total / (1024**3),
                "disk_used_gb": usage.used / (1024**3),
                "disk_free_gb": usage.free / (1024**3),
                "disk_used_percent": usage.percent,
            }

            for metric, value in metrics.items():
                doc = {
                    "@timestamp": now,
                    "share": share,
                    "metric": metric,
                    "value": round(value, 2),
                }
                es.index(index=index, document=doc)

            print(f"✅ Pushed metrics for {share}")

        except Exception as e:
            print(f"❌ Error with {share}: {e}")

# Example: Multiple network shares
network_shares = [r"Z:\\", r"Y:\\"]
push_disk_usage(network_shares)