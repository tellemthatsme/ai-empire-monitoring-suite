# 🚀 AI Empire API Documentation

## OpenRouter Integration & System APIs

### OpenRouter Configuration
- **Base URL**: `https://openrouter.ai/api/v1`
- **Authentication**: Bearer token authentication
- **Cost**: $0.00 (57 free models available)
- **Rate Limits**: 200 requests/minute per model
- **Status**: Connected (completion limitations detected)

### Available Free Models:
```json
{
  "free_models": [
    "deepseek/deepseek-chat-v3.1:free",
    "openai/gpt-oss-120b:free", 
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "google/gemma-2-2b-it:free",
    "microsoft/phi-3-mini-4k-instruct:free"
  ]
}
```

### System Health API
**Endpoint**: `/api/system/health`
**Method**: GET
**Response**:
```json
{
  "status": "operational",
  "health_score": 66.72,
  "active_alerts": 14,
  "auto_optimizations": 2,
  "uptime": "99.9%",
  "cost": 0.00
}
```

### Revenue Tracking API
**Endpoint**: `/api/revenue/current`
**Method**: GET
**Response**:
```json
{
  "week_1_projection": 30958,
  "month_1_projection": 123832,
  "quarter_1_projection": 371496,
  "services_ready": 5,
  "leads_generated": 100,
  "conversion_rate": 0.12
}
```

### Monitoring Systems API
**Endpoint**: `/api/monitoring/status`
**Method**: GET
**Response**:
```json
{
  "claude_monitor": "active",
  "performance_monitor": "active", 
  "cost_optimizer": "active",
  "mcp_server": "running",
  "total_monitors": 6
}
```

## Configuration Files

### Environment Configuration (.env)
```bash
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
USE_FREE_MODELS_ONLY=true

# System Configuration  
SYSTEM_PORT=8000
MEMORY_PERSISTENCE=true
AUTO_OPTIMIZATION=true
ZERO_COST_OPERATION=true
```

### MCP Server Configuration
```yaml
# mcp_agent.config.yaml
servers:
  memory_persistence:
    command: python
    args: [mcp-servers/mcp_memory_persistence_server.py]
    transport: stdio
  claude_code_server:
    command: python  
    args: [mcp-servers/enhanced_claude_code_mcp_server.py]
    transport: stdio
```

## API Endpoints Reference

### System Management
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/system/status` | GET | System health and status |
| `/api/system/optimize` | POST | Trigger optimization |
| `/api/system/restart` | POST | Restart services |

### Revenue Management  
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/revenue/projections` | GET | Revenue projections |
| `/api/revenue/services` | GET | Available services |
| `/api/revenue/leads` | GET | Lead generation data |

### Monitoring & Analytics
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/monitoring/metrics` | GET | Real-time metrics |
| `/api/monitoring/alerts` | GET | Active alerts |
| `/api/monitoring/performance` | GET | Performance data |

### Client Acquisition
| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/clients/leads` | GET | Generated leads |
| `/api/clients/campaigns` | GET | Campaign status |
| `/api/clients/conversion` | GET | Conversion metrics |

## Error Handling

### Standard Error Response:
```json
{
  "error": {
    "code": 400,
    "message": "Bad Request",
    "details": "Specific error information"
  }
}
```

### Common Error Codes:
- `400`: Bad Request
- `401`: Unauthorized (API key issues)
- `429`: Rate Limited
- `500`: Internal Server Error

## Authentication

### API Key Authentication:
```bash
# Header required for all requests
Authorization: Bearer your-api-key-here
Content-Type: application/json
```

### OpenRouter Authentication:
```bash
# For OpenRouter API calls
Authorization: Bearer sk-or-v1-your-openrouter-key
HTTP-Referer: https://github.com/tellemthatsme/ai-empire-monitoring-suite
X-Title: AI Empire Monitoring Suite
```

## Rate Limiting

### System API Limits:
- 1000 requests per hour
- 100 concurrent connections
- Burst limit: 50 requests/minute

### OpenRouter Limits:
- 200 requests/minute per model
- Free tier: Generous daily limits
- No cost for free models

## WebSocket Connections

### Real-time Updates:
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Listen for events
ws.on('system.update', (data) => {
  console.log('System update:', data);
});

ws.on('revenue.new', (data) => {
  console.log('New revenue:', data);
});
```

### WebSocket Events:
- `system.update`: System status changes
- `revenue.new`: New revenue events  
- `alert.triggered`: System alerts
- `performance.metrics`: Performance data

## SDK Examples

### Python SDK Usage:
```python
import requests

class AIEmpireAPI:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_system_status(self):
        response = requests.get(
            f'{self.base_url}/api/system/status',
            headers=self.headers
        )
        return response.json()
    
    def get_revenue_projections(self):
        response = requests.get(
            f'{self.base_url}/api/revenue/projections', 
            headers=self.headers
        )
        return response.json()
```

### JavaScript SDK Usage:
```javascript
class AIEmpireAPI {
    constructor(apiKey, baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async getSystemStatus() {
        const response = await fetch(`${this.baseUrl}/api/system/status`, {
            headers: this.headers
        });
        return await response.json();
    }
    
    async getRevenueProjections() {
        const response = await fetch(`${this.baseUrl}/api/revenue/projections`, {
            headers: this.headers  
        });
        return await response.json();
    }
}
```

## Testing & Development

### API Testing with curl:
```bash
# Test system status
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/api/system/status

# Test revenue projections  
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/api/revenue/projections
```

### Development Server:
```bash
# Start development server
python -m http.server 8000

# Start with API server
python api_server.py --port 8000 --debug
```

## Performance & Monitoring

### API Performance Metrics:
- Average response time: <200ms
- 99th percentile: <500ms  
- Uptime: 99.9%
- Error rate: <0.1%

### Monitoring Endpoints:
- `/health`: Health check endpoint
- `/metrics`: Prometheus metrics
- `/debug`: Debug information (dev only)

## Security Best Practices

### API Security:
- Always use HTTPS in production
- Rotate API keys regularly
- Implement rate limiting
- Validate all inputs
- Use proper CORS settings

### Data Protection:
- Encrypt sensitive data
- Use secure headers
- Implement proper authentication
- Log security events
- Regular security audits

---

**For API support**: Create an issue in the GitHub repository
**For integration help**: Check the SDK examples and documentation
**For enterprise features**: Contact for custom API development