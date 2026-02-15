# REST API Source Configuration Examples

## Table of Contents
- [Authentication Methods](#authentication-methods)
- [Pagination Types](#pagination-types)
- [Complete Examples](#complete-examples)

---

## Authentication Methods

### 1. API Key (Header)
```toml
[sources.example_api_key_header]
base_url = "https://api.example.com"
auth_type = "api_key"
api_key = "your_api_key_here"
api_key_name = "X-API-Key"          # Header name (default: X-API-Key)
api_key_location = "header"          # Location: header or query
```

### 2. API Key (Query Parameter)
```toml
[sources.example_api_key_query]
base_url = "https://api.example.com"
auth_type = "api_key"
api_key = "your_api_key_here"
api_key_name = "api_key"             # Query parameter name
api_key_location = "query"           # Put in URL query string
```

### 3. Bearer Token (OAuth 2.0)
```toml
[sources.github_api]
base_url = "https://api.github.com"
auth_type = "bearer"
token = "ghp_xxxxxxxxxxxxxxxxxxxx"   # GitHub Personal Access Token
rate_limit = 60                       # Optional: requests per minute
```

### 4. Basic Authentication
```toml
[sources.basic_auth_api]
base_url = "https://api.example.com"
auth_type = "basic"
username = "your_username"
password = "your_password"
```

### 5. OAuth 2.0 Client Credentials
```toml
[sources.oauth2_api]
base_url = "https://api.example.com"
auth_type = "oauth2"
oauth_url = "https://auth.example.com/oauth/token"
client_id = "your_client_id"
client_secret = "your_client_secret"
scope = "read:data"                  # Optional scope
```

### 6. No Authentication (Public API)
```toml
[sources.public_api]
base_url = "https://api.coingecko.com/api/v3"
auth_type = "none"
```

---

## Pagination Types

### 1. Single Page (No Pagination)
```toml
[sources.single_page_api]
base_url = "https://api.example.com"
pagination_type = "single_page"      # Or omit this line
```

### 2. Offset-Based Pagination
```toml
[sources.offset_api]
base_url = "https://api.example.com"
pagination_type = "offset"
page_size = 100                      # Records per page
offset_param = "offset"              # Offset parameter name (default: offset)
limit_param = "limit"                # Limit parameter name (default: limit)
maximum_offset = 10000               # Optional: prevent infinite loops

# Example requests:
# /api/data?limit=100&offset=0
# /api/data?limit=100&offset=100
# /api/data?limit=100&offset=200
```

### 3. Cursor-Based Pagination
```toml
[sources.stripe_api]
base_url = "https://api.stripe.com/v1"
auth_type = "bearer"
token = "sk_live_xxxxxxxxxxxx"
pagination_type = "cursor"
cursor_param = "starting_after"       # Cursor parameter name
cursor_path = "data[-1].id"           # Path to next cursor in response

# Example response:
# {
#   "data": [...],
#   "has_more": true,
#   "next_cursor": "cus_123abc"       # Extracted via cursor_path
# }
```

### 4. Page Number Pagination
```toml
[sources.page_number_api]
base_url = "https://api.example.com"
pagination_type = "page_number"
page_size = 50                       # Records per page
page_param = "page"                  # Page parameter name (default: page)
per_page_param = "per_page"          # Per-page parameter (default: per_page)
base_page = 1                        # Starting page: 0 or 1 (default: 1)
total_path = "meta.total_pages"      # Optional: path to total pages

# Example requests:
# /api/data?page=1&per_page=50
# /api/data?page=2&per_page=50
# /api/data?page=3&per_page=50
```

### 5. Header Link Pagination (GitHub Style)
```toml
[sources.github_api]
base_url = "https://api.github.com"
auth_type = "bearer"
token = "ghp_xxxxxxxxxxxx"
pagination_type = "header_link"      # RFC 5988 Link header
rate_limit = 60

# Example response headers:
# Link: <https://api.github.com/repos/o/r/issues?page=2>; rel="next",
#       <https://api.github.com/repos/o/r/issues?page=10>; rel="last"
```

### 6. JSON Link Pagination
```toml
[sources.json_link_api]
base_url = "https://api.example.com"
pagination_type = "json_link"
next_url_path = "links.next"         # Path to next URL in JSON response

# Example response:
# {
#   "data": [...],
#   "links": {
#     "next": "https://api.example.com/data?page=2",
#     "prev": "https://api.example.com/data?page=1"
#   }
# }

# Alternative nested structure:
next_url_path = "metadata.next_page.url"
# {
#   "data": [...],
#   "metadata": {
#     "next_page": {
#       "url": "..."
#     }
#   }
# }
```

---

## Complete Examples

### Example 1: GitHub Issues API
```toml
[sources.github_api]
base_url = "https://api.github.com"
auth_type = "bearer"
token = "ghp_xxxxxxxxxxxxxxxxxxxx"
pagination_type = "header_link"
rate_limit = 60                      # 60 requests per hour (GitHub limit)

# Excel Configuration:
# source_type: api
# source_name: github_api
# table_name: issues
# api_endpoint: /repos/owner/repo/issues
# pagination_type: header_link
# auth_type: bearer
# page_size: 100
# enabled: Y
```

### Example 2: Stripe Payments API
```toml
[sources.stripe_api]
base_url = "https://api.stripe.com/v1"
auth_type = "bearer"
token = "sk_live_xxxxxxxxxxxxxxxxxxxx"
pagination_type = "cursor"
cursor_param = "starting_after"
cursor_path = "data[-1].id"

# Excel Configuration:
# source_type: api
# source_name: stripe_api
# table_name: payments
# api_endpoint: /v1/charges
# pagination_type: cursor
# auth_type: bearer
# page_size: 100
# enabled: Y
```

### Example 3: CoinGecko Cryptocurrency API
```toml
[sources.coingecko_api]
base_url = "https://api.coingecko.com/api/v3"
auth_type = "api_key"
api_key = "CG-xxxxxxxxxxxxxxxxxxxx"
api_key_name = "x-cg-demo-api-key"
api_key_location = "header"
pagination_type = "offset"
page_size = 250
rate_limit = 10                      # 10 requests per minute (free tier)

# Excel Configuration:
# source_type: api
# source_name: coingecko_api
# table_name: crypto_markets
# api_endpoint: /coins/markets
# pagination_type: offset
# auth_type: api_key
# page_size: 250
# enabled: Y
```

### Example 4: JSONPlaceholder (Public API - No Auth)
```toml
[sources.jsonplaceholder_api]
base_url = "https://jsonplaceholder.typicode.com"
auth_type = "none"
pagination_type = "page_number"
page_size = 10
page_param = "_page"
per_page_param = "_limit"
base_page = 1

# Excel Configuration:
# source_type: api
# source_name: jsonplaceholder_api
# table_name: posts
# api_endpoint: /posts
# pagination_type: page_number
# auth_type: none
# page_size: 10
# enabled: Y
```

### Example 5: API with Nested Response (Data Selector)
```toml
[sources.nested_response_api]
base_url = "https://api.example.com"
auth_type = "bearer"
token = "your_token_here"
pagination_type = "offset"
data_selector = "data.items"         # Extract from nested structure

# Response structure:
# {
#   "success": true,
#   "data": {
#     "items": [...]                  # Actual data is here
#   },
#   "meta": {...}
# }

# Excel Configuration:
# source_type: api
# source_name: nested_response_api
# table_name: items
# api_endpoint: /api/v1/items
# data_selector: data.items
# pagination_type: offset
# auth_type: bearer
# enabled: Y
```

---

## Excel Configuration Template

Add these columns to your `ingestion_config.xlsx`:

| Column | Description | Example Values |
|--------|-------------|----------------|
| `api_endpoint` | API endpoint path | `/users`, `/repos/{owner}/{repo}/issues` |
| `pagination_type` | Pagination strategy | `offset`, `cursor`, `page_number`, `header_link`, `json_link`, `single_page` |
| `auth_type` | Authentication method | `none`, `api_key`, `bearer`, `basic`, `oauth2` |
| `page_size` | Records per page | `100`, `500`, `1000` |
| `data_selector` | Path to data array | `data.items`, `results`, `response.data` |
| `primary_key` | Primary key column(s) | `id`, `user_id`, `composite_key` |

---

## Rate Limiting

Control API request rate to avoid throttling:

```toml
[sources.rate_limited_api]
base_url = "https://api.example.com"
rate_limit = 30                      # Requests per minute
# Framework automatically paces requests
```

---

## Troubleshooting

### Issue: Getting Only First Page
**Solution**: Check pagination_type is set correctly in Excel or secrets

### Issue: Authentication Errors (401/403)
**Solution**: Verify token/key in secrets.toml, check expiration

### Issue: Rate Limit Errors (429)
**Solution**: Add or reduce `rate_limit` in secrets.toml

### Issue: Empty Results
**Solution**: Check `data_selector` if API returns nested responses

---

## Testing Your Configuration

```powershell
# Test single API job
cd dlt-ingestion-framework
C:\venv_dlt\Scripts\python.exe run.py

# Check logs for:
# [REST API] Pagination: offset
# [REST API] Base URL: https://api.example.com
# Rows processed: 1,500 (multiple pages loaded)
```
