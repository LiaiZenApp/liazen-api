# LiaiZen API Deployment Guide

This guide covers deploying the LiaiZen API in various environments with Docker.

## 🚀 Quick Deployment

### Development Environment

```bash
# Clone repository
git clone <repository-url>
cd gen_fastAPI-v2

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Production Environment

```bash
# Copy production environment file
cp .env.example .env.prod

# Edit production configuration
nano .env.prod

# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Monitor deployment
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔧 Environment-Specific Configurations

### Development (`docker-compose.yml`)

**Features:**
- Hot reloading enabled
- Debug mode active
- Database exposed on port 5432
- Adminer for database management
- Volume mounts for live code editing

**Services:**
- `api`: FastAPI application with auto-reload
- `db`: PostgreSQL database
- `redis`: Redis cache
- `adminer`: Database administration tool

### Production (`docker-compose.prod.yml`)

**Features:**
- Multi-worker deployment
- Resource limits and health checks
- Nginx reverse proxy
- Automated database backups
- Security hardening

**Services:**
- `api`: Production FastAPI with multiple workers
- `db`: PostgreSQL with backup automation
- `redis`: Redis cache
- `nginx`: Reverse proxy and SSL termination
- `db-backup`: Automated database backups

### Testing (`docker-compose.test.yml`)

**Features:**
- Isolated test environment
- Automated test execution
- Coverage reporting
- Clean database state

## 🏗️ Infrastructure Setup

### Prerequisites

1. **Docker & Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **System Requirements**
   - **Development**: 2GB RAM, 10GB disk space
   - **Production**: 4GB RAM, 50GB disk space
   - **CPU**: 2+ cores recommended

### Network Configuration

```bash
# Create external network (optional)
docker network create liaizen-network

# Use external network in compose files
networks:
  default:
    external:
      name: liaizen-network
```

## 🔒 Security Configuration

### SSL/TLS Setup

1. **Generate SSL certificates**
   ```bash
   # Create SSL directory
   mkdir -p nginx/ssl
   
   # Generate self-signed certificate (development)
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/server.key \
     -out nginx/ssl/server.crt
   
   # For production, use Let's Encrypt
   certbot certonly --webroot -w /var/www/html -d api.liaizen.com
   ```

2. **Configure Nginx**
   ```nginx
   # nginx/nginx.conf
   server {
       listen 443 ssl;
       server_name api.liaizen.com;
       
       ssl_certificate /etc/nginx/ssl/server.crt;
       ssl_certificate_key /etc/nginx/ssl/server.key;
       
       location / {
           proxy_pass http://api:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Environment Security

1. **Secure environment variables**
   ```bash
   # Generate secure JWT secret
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Generate secure database password
   openssl rand -base64 32
   ```

2. **File permissions**
   ```bash
   # Secure environment files
   chmod 600 .env .env.prod
   
   # Secure SSL certificates
   chmod 600 nginx/ssl/*
   ```

## 🌐 Cloud Deployment

### Azure Container Instances

1. **Build and push image**
   ```bash
   # Login to Azure
   az login
   
   # Create container registry
   az acr create --resource-group myResourceGroup --name myregistry --sku Basic
   
   # Build and push
   az acr build --registry myregistry --image liaizen-api:latest .
   ```

2. **Deploy container**
   ```bash
   # Create container instance
   az container create \
     --resource-group myResourceGroup \
     --name liaizen-api \
     --image myregistry.azurecr.io/liaizen-api:latest \
     --cpu 2 --memory 4 \
     --ports 8000 \
     --environment-variables \
       DATABASE_URL=$DATABASE_URL \
       AUTH0_DOMAIN=$AUTH0_DOMAIN \
       JWT_SECRET_KEY=$JWT_SECRET_KEY
   ```

### AWS ECS

1. **Create task definition**
   ```json
   {
     "family": "liaizen-api",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "containerDefinitions": [
       {
         "name": "api",
         "image": "your-account.dkr.ecr.region.amazonaws.com/liaizen-api:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "postgresql://..."
           }
         ]
       }
     ]
   }
   ```

### Kubernetes

1. **Create deployment**
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: liaizen-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: liaizen-api
     template:
       metadata:
         labels:
           app: liaizen-api
       spec:
         containers:
         - name: api
           image: liaizen-api:latest
           ports:
           - containerPort: 8000
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: liaizen-secrets
                 key: database-url
           resources:
             requests:
               memory: "512Mi"
               cpu: "250m"
             limits:
               memory: "1Gi"
               cpu: "500m"
   ```

## 📊 Monitoring and Logging

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Check database connectivity
docker-compose exec db pg_isready -U user -d liaizen

# Check all services
docker-compose ps
```

### Log Management

```bash
# View application logs
docker-compose logs -f api

# View database logs
docker-compose logs -f db

# Export logs
docker-compose logs --no-color api > app.log
```

### Monitoring Setup

1. **Prometheus metrics**
   ```yaml
   # Add to docker-compose.prod.yml
   prometheus:
     image: prom/prometheus
     ports:
       - "9090:9090"
     volumes:
       - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
   
   grafana:
     image: grafana/grafana
     ports:
       - "3000:3000"
     environment:
       - GF_SECURITY_ADMIN_PASSWORD=admin
   ```

## 🔄 Backup and Recovery

### Database Backups

```bash
# Manual backup
docker-compose exec db pg_dump -U user liaizen > backup.sql

# Automated backup (included in production compose)
# Backups are created daily and stored in ./backups/

# Restore from backup
docker-compose exec -T db psql -U user liaizen < backup.sql
```

### Volume Backups

```bash
# Backup volumes
docker run --rm -v liaizen_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volumes
docker run --rm -v liaizen_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## 🚨 Troubleshooting

### Common Issues

1. **Database connection errors**
   ```bash
   # Check database status
   docker-compose exec db pg_isready
   
   # Check network connectivity
   docker-compose exec api ping db
   
   # Verify environment variables
   docker-compose exec api env | grep DATABASE
   ```

2. **Memory issues**
   ```bash
   # Check container resource usage
   docker stats
   
   # Increase memory limits in compose file
   deploy:
     resources:
       limits:
         memory: 2G
   ```

3. **SSL certificate issues**
   ```bash
   # Verify certificate
   openssl x509 -in nginx/ssl/server.crt -text -noout
   
   # Test SSL connection
   openssl s_client -connect localhost:443
   ```

### Performance Optimization

1. **Database optimization**
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_connections_user_id ON connections(user_id);
   ```

2. **Application optimization**
   ```bash
   # Increase worker count
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   
   # Enable connection pooling
   DATABASE_URL=postgresql+asyncpg://user:pass@host/db?pool_size=20&max_overflow=0
   ```

## 📋 Deployment Checklist

### Pre-deployment

- [ ] Update environment variables in `.env.prod`
- [ ] Generate secure JWT secret key
- [ ] Configure Auth0 production settings
- [ ] Set up SSL certificates
- [ ] Configure database credentials
- [ ] Test backup and restore procedures

### Deployment

- [ ] Build production Docker image
- [ ] Deploy database first
- [ ] Run database migrations
- [ ] Deploy application
- [ ] Configure reverse proxy
- [ ] Set up monitoring
- [ ] Configure log aggregation

### Post-deployment

- [ ] Verify health checks
- [ ] Test API endpoints
- [ ] Monitor resource usage
- [ ] Set up alerting
- [ ] Document deployment process
- [ ] Train operations team

## 🔗 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Nginx Configuration](https://nginx.org/en/docs/)