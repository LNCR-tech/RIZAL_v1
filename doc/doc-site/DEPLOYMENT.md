# Aura Documentation - Deployment Guide

## Quick Start

### Development
```bash
npm install
npm start
```

Visit: `http://localhost:3000`

### Production Build
```bash
npm run build:prod
npm run serve
```

### Docker Deployment

#### Build and Run
```bash
# Build image
docker build -t aura-doc-site .

# Run container
docker run -p 3000:80 aura-doc-site
```

#### Using Docker Compose
```bash
docker compose up --build
```

#### Using Deployment Script

**Linux/Mac**:
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows**:
```cmd
deploy.bat
```

## Environment Configuration

### Development (`.env.development`)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_AUTH_ENABLED=false
REACT_APP_DEFAULT_ROLE=admin
```

### Production (`.env.production`)
```env
REACT_APP_BACKEND_URL=https://api.aura.school
REACT_APP_AUTH_ENABLED=true
REACT_APP_DEFAULT_ROLE=student
```

## Integration with Main Project

Add to root `docker-compose.yml`:

```yaml
services:
  doc-site:
    build:
      context: ./doc-site
      dockerfile: Dockerfile
    container_name: aura-doc-site
    ports:
      - "3000:80"
    environment:
      - REACT_APP_BACKEND_URL=http://backend:8001
      - REACT_APP_AUTH_ENABLED=true
    depends_on:
      - backend
    networks:
      - aura-network
    profiles:
      - docs
      - full
```

Start with:
```bash
docker compose --profile docs up
```

## Health Check

```bash
curl http://localhost:3000/health
```

Expected response: `healthy`

## Troubleshooting

### Build Fails
```bash
# Clear cache
npm run clear
rm -rf node_modules
npm install
```

### Docker Build Fails
```bash
# Clear Docker cache
docker builder prune
docker build --no-cache -t aura-doc-site .
```

### Container Won't Start
```bash
# Check logs
docker logs aura-doc-site

# Check health
docker inspect aura-doc-site | grep Health
```

## Production Checklist

- [ ] Set production environment variables
- [ ] Configure SSL/TLS certificates
- [ ] Set up domain (docs.aura.school)
- [ ] Configure reverse proxy (Nginx/Traefik)
- [ ] Test authentication with production backend
- [ ] Verify all links work
- [ ] Check mobile responsiveness
- [ ] Test search functionality
- [ ] Monitor performance metrics
- [ ] Set up error tracking

## Monitoring

### Docker Stats
```bash
docker stats aura-doc-site
```

### Logs
```bash
# Follow logs
docker logs -f aura-doc-site

# Last 100 lines
docker logs --tail 100 aura-doc-site
```

### Health Status
```bash
# Check health
docker inspect --format='{{.State.Health.Status}}' aura-doc-site
```

## Maintenance

### Update Documentation
1. Edit files in `docs/`
2. Commit changes
3. Rebuild and redeploy:
   ```bash
   ./deploy.sh
   ```

### Update Dependencies
```bash
npm update
npm audit fix
```

### Backup
```bash
# Backup documentation
tar -czf docs-backup-$(date +%Y%m%d).tar.gz docs/
```

## Performance

### Build Size
```bash
# Check build size
du -sh build/

# Analyze bundle
npm run build -- --analyze
```

### Optimization Tips
- Enable gzip compression (already configured in nginx.conf)
- Use CDN for static assets
- Enable browser caching
- Minimize JavaScript bundles
- Optimize images

## Security

### Headers
Security headers are configured in `nginx.conf`:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

### HTTPS
For production, configure SSL:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of config
}
```

## Support

- Documentation: See `doc/docusaurus-manual/`
- Issues: Contact dev team
- Updates: Check GitHub releases
