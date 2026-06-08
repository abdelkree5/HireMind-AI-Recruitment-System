# RabbitMQ Performance Impact Report

## Expected impact

### Latency

Moving agent coordination from synchronous in-process calls to RabbitMQ introduces an additional broker hop.
However, durable queues and asynchronous workers improve throughput and protect against backpressure.

### Throughput

- Agent tasks are decoupled and can scale independently.
- RabbitMQ workers can horizontally scale by adding more consumers.
- Throughput is bounded by broker capacity and consumer processing latency.

### Resource usage

- CPU and memory shift from the API process to worker processes.
- RabbitMQ adds network and broker memory overhead.
- Persistent queues consume disk I/O for durable messages.

## Observability targets

Track these metrics:

- `queue_depth`: number of ready messages in each queue.
- `retry_count`: number of times a message was retried.
- `dlq_count`: number of messages in dead-letter queues.
- `processing_latency`: end-to-end time from publish to acknowledgment.
- `failed_messages`: count of failed messages per agent.
- `consumer_count`: active consumer count per queue.

## Metrics integration

The platform now exposes RabbitMQ queue metrics through:

- `ai_engine.observability.rabbitmq_metrics.get_rabbitmq_queue_metrics()`
- `backend.app.routes.agents.get_agent_status()` includes `rabbitmq_metrics`

## Performance considerations

### Warm-up

- First messages after a cold start may be slower.
- Persistent connections and predeclared queues help stabilize latency.

### Retry behavior

- Exponential backoff reduces load during transient failure windows.
- Retry queue depth should be monitored to avoid retry storms.

### DLQ handling

- DLQ growth indicates repeated failures or schema drift.
- DLQ counts should trigger automated alerts for investigation.

## Recommendations

- Run a load test with realistic workflow volumes and measure p50/p95/p99 latency.
- Use the queue depth and DLQ counts to tune worker concurrency and prefetch settings.
- Monitor RabbitMQ broker CPU, memory, and disk usage during peak processing.
- Correlate `agent_traces` latency with queue metrics to identify bottlenecks.
