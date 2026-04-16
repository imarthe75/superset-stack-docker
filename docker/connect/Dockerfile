FROM debezium/connect:latest

USER root
RUN yum install -y unzip

# Instalar ClickHouse Sink Connector
# Usamos la versión estable del conector oficial de ClickHouse
RUN curl -L https://github.com/ClickHouse/clickhouse-kafka-connect/releases/download/v1.1.2/clickhouse-kafka-connect-v1.1.2.zip -o clickhouse-sink.zip && \
    mkdir -p /kafka/connect/clickhouse-sink && \
    unzip clickhouse-sink.zip -d /kafka/connect/clickhouse-sink && \
    rm clickhouse-sink.zip

USER kafka
