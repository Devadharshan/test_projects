def push_metric(keyword_type, keyword_value, count, file_path, line_number):
    filename = file_path.split("/")[-1]
    folder = "/".join(file_path.split("/")[:-1]) or "/"

    registry = CollectorRegistry()

    # Clean, safe metric name
    metric_name = safe_metric_name(f"log_occurrence_{keyword_type}_{keyword_value}")
    description = f"Occurrences of {keyword_type}: {keyword_value}"

    g = Gauge(
        metric_name,
        description,
        labelnames=["context"],
        registry=registry
    )

    context_label = (
        f"app={APP_NAME}, env={ENV}, type={keyword_type}, keyword={keyword_value}, "
        f"file={filename}, folder={folder}, line={line_number}"
    )

    g.labels(context=context_label).set(count)

    try:
        push_to_gateway(
            PUSHGATEWAY_URL,
            job=f"{APP_NAME}_log_monitor",
            registry=registry
        )
    except Exception as e:
        logging.error(f"❌ Failed to push metric {metric_name}: {e}")