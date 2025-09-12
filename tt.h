metricbeat.modules:
  - module: system
    metricsets:
      - cpu
      - memory
      - network
      - diskio
      - filesystem
    enabled: true
    period: 10s

output.elasticsearch:
  hosts: ["https://localhost:9200"]
  username: "elastic"
  password: "<your_elastic_password>"
  ssl.verification_mode: none