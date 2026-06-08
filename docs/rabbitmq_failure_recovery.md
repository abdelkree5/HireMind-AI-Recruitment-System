# RabbitMQ Failure Recovery Report

## Objectives

Validate that RabbitMQ integration preserves workflow state during failure and recovery:

- Agent crash
- RabbitMQ restart
- Message loss
- Consumer failure

## Recovery design

### Durable queues

All agent queues are declared durable, so in-flight messages remain in the broker across restarts.

### Acknowledgements

Agents acknowledge messages only after execution succeeds.
Failed deliveries are not acked and are routed through retry logic.

### Retry policy

- Each failed message increments `x-retry-count`.
- Retries use exponential backoff: 1s, 2s, 4s, 8s, ... up to 30s.
- After `MAX_RETRY_ATTEMPTS` the message moves to the DLQ.

### Dead letter queue (DLQ)

- DLQs capture poison messages and unrecoverable failures.
- Each DLQ includes `x-retry-count` and `poison` metadata.
- DLQ messages can be reviewed and reprocessed manually.

### Workflow recovery

- `domain_events` records workflow milestones.
- `agent_messages` preserves the audit trail for each workflow.
- Supervisor recovery can replay events from `domain_events` and resume the next state.

## Simulation scenarios

### Agent crash

1. Start the system with RabbitMQ enabled.
2. Publish a workflow task to the supervisor exchange.
3. Kill the worker process for a target agent.
4. Ensure the task remains in the queue and is redelivered when the worker restarts.

Expected result:

- No message loss.
- Task is processed when the worker comes back.
- Retry counts are preserved.

### RabbitMQ restart

1. Start the system and publish a workflow event.
2. Stop RabbitMQ and restart it.
3. Confirm durable queues are restored.
4. Resume processing once RabbitMQ is available.

Expected result:

- Durable queues retain messages.
- In-flight tasks on unacked deliveries return to queue.
- Workflow continues without requiring application redeployment.

### Message loss

1. Force an invalid message payload or worker failure.
2. Confirm the broker moves the message to DLQ after max retries.
3. Verify `domain_events` still contains prior workflow state.

Expected result:

- No silent message loss.
- Poison messages are visible in DLQ.
- Event audit trail remains intact.

### Consumer failure

1. Remove a consumer while messages are pending.
2. Confirm the broker requeues unacked messages.
3. Restart the consumer and validate processing resumes.

Expected result:

- Messages are not lost.
- Queue depth drops once consumers return.
- Failure counts and retry counts are observable.

## Observability signals

Track these metrics for recovery verification:

- Queue depth
- Retry queue depth
- DLQ depth
- Message processing latency
- Failed message count
- Recoverable failure rate

## Notes

- Event persistence in `domain_events` enables replay if a workflow needs reconstruction.
- The current system uses `ai_engine.observability.rabbitmq_metrics.get_rabbitmq_queue_metrics()` to expose queue depth and DLQ counts.
- Manual reprocessing strategies should be built for DLQ inspection and remediation.
