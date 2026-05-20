import asyncio
import dns.resolver
import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

app = FastAPI(
    title="Subdomain Enumerator",
    description="Discover subdomains for any domain with DNS resolution and HTTP status checks.",
    version="1.0.0"
)

# Common subdomain wordlist
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2",
    "ns3", "ns4", "imap", "api", "dev", "test", "staging", "demo", "admin",
    "portal", "secure", "vpn", "m", "mobile", "app", "shop", "store", "blog",
    "news", "support", "help", "forum", "wiki", "docs", "cdn", "media",
    "assets", "static", "images", "img", "css", "js", "scripts", "fonts",
    "download", "downloads", "files", "upload", "uploads", "backup",
    "backups", "db", "database", "sql", "mysql", "postgres", "mongo",
    "redis", "elastic", "elasticsearch", "kibana", "log", "logs",
    "monitor", "monitoring", "status", "health", "metrics", "prometheus",
    "grafana", "zipkin", "jaeger", "trace", "tracing", "api-v1", "api-v2",
    "v1", "v2", "v3", "prod", "production", "beta", "alpha", "gamma",
    "release", "preview", "edge", "internal", "intranet", "private",
    "corp", "corporate", "enterprise", "business", "partner", "partners",
    "client", "clients", "customer", "customers", "user", "users",
    "account", "accounts", "auth", "login", "signin", "signup", "register",
    "sso", "oauth", "oauth2", "oidc", "saml", "ldap", "ad", "active-directory",
    "web", "website", "site", "home", "main", "start", "landing",
    "info", "about", "contact", "contacts", "team", "staff", "careers",
    "jobs", "hire", "hr", "payroll", "finance", "accounting", "billing",
    "invoice", "invoices", "payment", "payments", "pay", "checkout",
    "cart", "order", "orders", "purchase", "purchases", "receipt",
    "shipping", "delivery", "track", "tracking", "logistics", "supply",
    "warehouse", "inventory", "stock", "product", "products", "catalog",
    "category", "categories", "item", "items", "sku", "variant", "option",
    "search", "find", "query", "suggest", "autocomplete", "recommend",
    "related", "similar", "compare", "filter", "sort", "rank", "rating",
    "review", "reviews", "comment", "comments", "feedback", "survey",
    "poll", "vote", "rating", "star", "like", "favorite", "bookmark",
    "save", "share", "email", "sms", "notification", "notify", "alert",
    "push", "websocket", "socket", "io", "stream", "streaming", "live",
    "realtime", "event", "events", "webhook", "hook", "callback",
    "proxy", "reverse-proxy", "load-balancer", "lb", "gateway", "ingress",
    "router", "switch", "hub", "firewall", "waf", "ids", "ips",
    "scanner", "scan", "audit", "auditor", "check", "checker", "tester",
    "validator", "verify", "verification", "validate", "inspection",
    "inspector", "reviewer", "assessment", "compliance", "soc2", "iso",
    "gdpr", "hipaa", "pci", "security", "secure", "protection", "protect",
    "shield", "guard", "defender", "antivirus", "malware", "threat",
    "risk", "vulnerability", "vuln", "exploit", "attack", "breach",
    "incident", "response", "forensics", "investigation", "detective",
    "analytics", "analytic", "insight", "intelligence", "intel",
    "report", "reporting", "dashboard", "board", "panel", "console",
    "ui", "gui", "interface", "view", "viewer", "preview", "render",
    "generate", "generator", "build", "builder", "deploy", "deployment",
    "ci", "cd", "pipeline", "pipeline", "jenkins", "gitlab", "github",
    "bitbucket", "docker", "container", "container", "kubernetes", "k8s",
    "helm", "rancher", "openshift", "swarm", "compose", "stack", "service",
    "microservice", "microservices", "mesh", "istio", "linkerd", "consul",
    "vault", "nomad", "terraform", "pulumi", "ansible", "puppet", "chef",
    "salt", "vagrant", "packer", "cloud", "aws", "azure", "gcp", "google",
    "digitalocean", "do", "linode", "vultr", "heroku", "netlify", "vercel",
    "cloudflare", "cf", "fastly", "akamai", "edgecast", "maxcdn", "keycdn",
    "bunny", "imagekit", "imgix", "cloudinary", "twilio", "sendgrid",
    "mailgun", "mailchimp", "postmark", "sparkpost", "aws-ses", "ses",
    "sns", "sqs", "lambda", "s3", "ec2", "rds", "dynamodb", "redshift",
    "elasticache", "cloudfront", "route53", "elb", "alb", "nlb", "ecr",
    "ecs", "eks", "fargate", "batch", "glue", "athena", "emr", "kinesis",
    "kafka", "msk", "rabbitmq", "amqp", "mqtt", "grpc", "graphql",
    "rest", "soap", "xml", "json", "yaml", "toml", "ini", "csv", "tsv",
    "parquet", "orc", "avro", "protobuf", "proto", "thrift", "capnp",
    "flatbuffers", "msgpack", "bson", "ubjson", "cbor", "smile", "ion"
]

class SubdomainRequest(BaseModel):
    domain: str
    wordlist: Optional[List[str]] = None
    check_http: bool = True
    timeout: int = 5

class SubdomainResult(BaseModel):
    subdomain: str
    resolved: bool
    ip_addresses: List[str]
    http_status: Optional[int] = None
    http_title: Optional[str] = None
    error: Optional[str] = None

class SubdomainResponse(BaseModel):
    domain: str
    total_checked: int
    found: int
    subdomains: List[SubdomainResult]
    wildcard_detected: bool
    timestamp: str
    execution_time: float

@app.get("/")
def root():
    return {
        "service": "Subdomain Enumerator",
        "version": "1.0.0",
        "endpoints": {
            "enumerate": "POST /enumerate — Discover subdomains",
            "health": "GET /health — Check service status"
        },
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

async def check_dns(subdomain: str, timeout: int):
    """Check if subdomain resolves via DNS."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        answers = resolver.resolve(subdomain, 'A')
        ips = [str(rdata) for rdata in answers]
        return True, ips, None
    except Exception as e:
        return False, [], str(e)

async def check_http_status(subdomain: str, timeout: int):
    """Check HTTP status code and title."""
    urls = [f"http://{subdomain}", f"https://{subdomain}"]
    
    for url in urls:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url, allow_redirects=True, ssl=False) as response:
                    status = response.status
                    text = await response.text()
                    # Extract title
                    title = None
                    if '<title>' in text.lower():
                        start = text.lower().find('<title>') + 7
                        end = text.lower().find('</title>')
                        if end > start:
                            title = text[start:end].strip()
                    return status, title, None
        except Exception:
            continue
    
    return None, None, "HTTP check failed"

async def check_wildcard(domain: str):
    """Detect wildcard DNS (e.g., *.example.com)."""
    test_sub = f"this-should-not-exist-{hash(domain) % 10000}.{domain}"
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 3
        resolver.resolve(test_sub, 'A')
        return True
    except:
        return False

@app.post("/enumerate")
async def enumerate_subdomains(request: SubdomainRequest):
    start_time = datetime.datetime.utcnow()
    domain = request.domain.lower().strip()
    
    # Clean domain
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
    
    # Use provided wordlist or default
    wordlist = request.wordlist if request.wordlist else COMMON_SUBDOMAINS
    
    # Check for wildcard DNS
    wildcard = await check_wildcard(domain)
    
    # Generate subdomains to check
    subdomains_to_check = [f"{sub}.{domain}" for sub in wordlist]
    
    # Async check all subdomains
    results = []
    tasks = []
    
    for sub in subdomains_to_check:
        tasks.append(process_subdomain(sub, request.check_http, request.timeout))
    
    subdomain_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in subdomain_results:
        if isinstance(result, Exception):
            continue
        if result:
            results.append(result)
    
    execution_time = (datetime.datetime.utcnow() - start_time).total_seconds()
    
    return {
        "domain": domain,
        "total_checked": len(subdomains_to_check),
        "found": len(results),
        "subdomains": results,
        "wildcard_detected": wildcard,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "execution_time": round(execution_time, 2)
    }

async def process_subdomain(subdomain: str, check_http: bool, timeout: int):
    """Process a single subdomain check."""
    resolved, ips, dns_error = await check_dns(subdomain, timeout)
    
    if not resolved:
        return None
    
    http_status = None
    http_title = None
    http_error = None
    
    if check_http:
        http_status, http_title, http_error = await check_http_status(subdomain, timeout)
    
    return {
        "subdomain": subdomain,
        "resolved": True,
        "ip_addresses": ips,
        "http_status": http_status,
        "http_title": http_title,
        "error": http_error if http_error and not http_status else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
