# Test Suite for USYD Web Crawler and RAG

This directory contains all test scripts for the USYD Web Crawler and RAG application.

## Test Files

- `test_api.py` - API endpoint testing
- `test_auth.py` - Authentication system testing
- `test_basic.py` - Basic application functionality testing
- `test_openai_config.py` - OpenAI configuration and integration testing
- `test_scraper.py` - Web scraping functionality testing

## Running Tests

To run all tests:
```bash
cd /workspaces/USD Web Crawler and RAG
python -m pytest tests/
```

To run a specific test file:
```bash
python -m pytest tests/test_api.py
```

To run tests with verbose output:
```bash
python -m pytest tests/ -v
```

## Test Requirements

Make sure to install the required dependencies:
```bash
pip install pytest pytest-cov
```

## Note

All tests should use real data and actual API calls as per the project's testing philosophy. Mock data should be avoided except for isolated utility function tests.
