# Tests

## Running tests

From project root:

```bash
uv run pytest tests/ -v
```

With coverage:

```bash
uv run pytest tests/ --cov=src --cov-report=html
```

Parallel:

```bash
uv run pytest tests/ -n auto
```

## Forum-topics suite

Primary unit tests are in `tests/test_forum_topics_minimal.py`.

Run only forum tests:

```bash
uv run pytest tests/test_forum_topics_minimal.py -v
```

## Optional live integration test (forum topics)

There is one opt-in integration test:
- `test_list_forum_topics_live_api_shape`

It is skipped by default. Enable with:

```bash
FAST_MCP_TELEGRAM_LIVE_TESTS=1 \
FAST_MCP_TELEGRAM_FORUM_CHAT_ID=<chat_id> \
uv run pytest tests/test_forum_topics_minimal.py -m integration -v
```

This verifies real Telegram API response shape for forum topics without making CI flaky.
