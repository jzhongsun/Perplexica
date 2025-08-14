#!/bin/bash

export OTEL_SERVICE_NAME=danus-agents
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://tracing-analysis-dc-hz.aliyuncs.com:8090
export OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://tracing-analysis-dc-hz.aliyuncs.com:8090
export OTEL_EXPORTER_OTLP_HEADERS=Authentication=bl4pzfjnli@ecc10e7cc577536_bl4pzfjnli@53df7ad2afe8301

uvicorn main:app --host=0.0.0.0 --port=8000