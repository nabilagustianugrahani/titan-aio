# TITAN AIO — Testing Rules

## Requirements
Every module requires:
1. **Unit tests** — test logic in isolation
2. **Integration tests** — test module + dependencies
3. **Error handling tests** — test failure modes

## Coverage Target: >80%

## Test Structure
Tests mirror the source tree:
```
Tests/
├── test_imports.py        # All modules import cleanly
├── test_schemas.py        # Pydantic validation
├── test_mcp_tools.py      # MCP tool functions
├── test_agents.py         # Agent classes
├── test_workers.py        # Worker classes
├── test_integration.py    # End-to-end flows
├── test_notion.py         # Notion integration
└── conftest.py            # Fixtures, SQLite override
```

## Patterns

### 1. Database tests
```python
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
# conftest.py handles table creation automatically
```

### 2. Async tests
```python
@pytest.mark.asyncio
async def test_something():
    result = await some_async_func()
    assert result.status == "ok"
```

### 3. Schema validation tests
```python
def test_invalid_input():
    with pytest.raises(ValidationError):
        SomeSchema(invalid_field="")
```

### 4. Integration tests
```python
@pytest.mark.asyncio
async def test_full_pipeline():
    ceo = CEOAgent()
    package = await ceo.create_affiliate_package(url)
    assert package.product.title
    assert len(package.hooks) > 0
```

## Running Tests
```bash
# All tests
python -m pytest Tests/ -v

# Specific file
python -m pytest Tests/test_mcp_tools.py -v

# With coverage
python -m pytest Tests/ --cov=.
```

## CI (Future)
- Run on every PR
- Block merge if tests fail
- Block merge if coverage drops
