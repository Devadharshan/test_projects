def push_metric(keyword_type, keyword_value, count, file_path, label_type="realtime"):
    # Extract path components
    path = file_path
    filename = file_path.split("/")[-1]
    folder = "/".join(file_path.split("/")[:-1]) or "/"

    # Prometheus setup
    registry = CollectorRegistry()
    g = Gauge(
        'log_keyword_occurrences',
        'Count of keyword occurrences in logs',
        labelnames=[
            "app_name", "env", "keyword_type", "keyword",
            "filename", "folder", "path", "date", "mode"
        ],
        registry=registry
    )

    # Apply labels with separate variables
    g.labels(
        app_name=APP_NAME,
        env=ENV,
        keyword_type=keyword_type,
        keyword=keyword_value,
        filename=filename,
        folder=folder,
        path=path,
        date=datetime.now().strftime("%Y-%m-%d"),
        mode=label_type
    ).set(count)

    # Push to PushGateway
    job_name = f"{APP_NAME}_{ENV}_log_monitor"
    try:
        push_to_gateway(PUSHGATEWAY_URL, job=job_name, registry=registry)
        print(f"[+] Pushed {keyword_type}: {keyword_value}={count} from {path}")
    except Exception as e:
        print(f"[ERROR] Failed to push metrics: {e}")