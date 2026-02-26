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

## Optional live integration tests (forum topics)

Opt-in tests:
- `test_list_forum_topics_live_api_shape`
- `test_list_forum_topics_live_limit_20_semantics`
- `test_list_forum_topics_live_limit_100_semantics`

Disabled by default. Run manually:

```bash
FAST_MCP_TELEGRAM_LIVE_TESTS=1 \
FAST_MCP_TELEGRAM_FORUM_CHAT_ID=<chat_id> \
uv run pytest tests/test_forum_topics_minimal.py -m integration -v
```

These tests validate real API shape and `has_more` behavior for `topics_limit=20` and `topics_limit=100`.
