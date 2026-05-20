# Subdomain Enumerator API

Discover subdomains for any domain with DNS resolution and HTTP status checks.

## Public URL

**Base URL:** `https://subdomain-enumerator-api.onrender.com`

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| POST | `/enumerate` | Enumerate subdomains |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | OpenAPI spec |

## API Usage

### Enumerate Subdomains

```bash
curl -X POST https://subdomain-enumerator-api.onrender.com/enumerate \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com", "check_http": true}'
```

### Response

```json
{
  "domain": "google.com",
  "total_checked": 500,
  "found": 42,
  "subdomains": [
    {
      "subdomain": "www.google.com",
      "resolved": true,
      "ip_addresses": ["142.250.80.46"],
      "http_status": 200,
      "http_title": "Google",
      "error": null
    }
  ],
  "wildcard_detected": false,
  "timestamp": "2026-05-20T22:00:00",
  "execution_time": 12.5
}
```

## Features

- **DNS Resolution**: Checks if subdomains resolve to IP addresses
- **HTTP Status**: Optionally checks HTTP/HTTPS status codes and page titles
- **Wildcard Detection**: Identifies wildcard DNS configurations
- **Custom Wordlist**: Use built-in (500+ common subdomains) or provide your own
- **Fast**: Async processing for quick enumeration

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Docker

```bash
docker build -t subdomain-enumerator .
docker run -p 8000:8000 subdomain-enumerator
```

## License

MIT
