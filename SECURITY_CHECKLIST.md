# 🔒 AURA PRODUCTION SECURITY CHECKLIST

## ⚠️ CRITICAL - BEFORE DEPLOYMENT

### 1. Secrets Management
- [ ] **NEVER commit .env file to git** - Add to .gitignore
- [ ] Generate strong SECRET_KEY: `openssl rand -hex 32`
- [ ] Generate strong DB_PASSWORD: `openssl rand -base64 32`
- [ ] Generate strong PGADMIN_PASSWORD: `openssl rand -base64 24`
- [ ] Obtain valid AI_API_KEY from your provider
- [ ] Obtain valid MAILJET_API_KEY and MAILJET_API_SECRET
- [ ] Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables (minimum 12 chars, mixed case, numbers, symbols)

### 2. Environment Configuration
- [ ] Copy `.env.secure.example` to `.env`
- [ ] Replace ALL placeholder values with real credentials
- [ ] Set `API_DOCS_ENABLED=false` in production
- [ ] Set `RATE_LIMIT_FAIL_OPEN=false` in production
- [ ] Configure `TRUSTED_HOSTS` with your actual domain names
- [ ] Update `CORS_ALLOWED_ORIGINS` with your frontend domain only
- [ ] Set proper `LOGIN_URL`, `BACKEND_ORIGIN`, `ASSISTANT_ORIGIN` with HTTPS URLs

### 3. Database Security
- [ ] Change default database name from `fastapi_db` to something unique
- [ ] Change default database user from `postgres` to a custom username
- [ ] Use strong, unique database password (32+ characters)
- [ ] Restrict database access to application containers only
- [ ] Enable database connection encryption (SSL/TLS)
- [ ] Configure database backups with encryption

### 4. Network Security
- [ ] Use HTTPS/TLS for all public endpoints (frontend, backend, assistant)
- [ ] Configure reverse proxy (nginx/traefik) with SSL certificates
- [ ] Restrict database port (5432) - do not expose publicly
- [ ] Restrict Redis port (6379) - do not expose publicly
- [ ] Restrict pgAdmin port (5050) - use SSH tunnel or VPN only
- [ ] Configure firewall rules (allow only 80/443 publicly)
- [ ] Enable AWS Security Groups with minimal required ports

### 5. Docker Security
- [ ] All containers run as non-root users ✓ (already implemented)
- [ ] Remove or secure pgAdmin in production (consider removing entirely)
- [ ] Use Docker secrets for sensitive data instead of environment variables
- [ ] Scan images for vulnerabilities: `docker scan <image>`
- [ ] Use specific image tags, not `latest`
- [ ] Limit container resources (CPU, memory)

### 6. Application Security
- [ ] Disable API documentation in production (`API_DOCS_ENABLED=false`)
- [ ] Enable rate limiting (`RATE_LIMIT_ENABLED=true`)
- [ ] Set strict CORS origins (no wildcards)
- [ ] Configure trusted hosts (no `*` wildcard)
- [ ] Enable face verification for privileged operations
- [ ] Review and remove demo/seed credentials

### 7. File Security
- [ ] Delete `Backend/storage/seed_credentials.csv` before deployment
- [ ] Ensure `.gitignore` includes `.env` and all credential files
- [ ] Remove any test/demo accounts from database
- [ ] Secure file upload directories with proper permissions
- [ ] Limit file upload sizes (already configured)

### 8. Monitoring & Logging
- [ ] Set up centralized logging (ELK, CloudWatch, etc.)
- [ ] Enable audit logging for sensitive operations
- [ ] Monitor failed login attempts
- [ ] Set up alerts for security events
- [ ] Configure log rotation and retention
- [ ] Monitor rate limit violations

### 9. Email Security
- [ ] Verify domain with SPF, DKIM, DMARC records
- [ ] Use verified sender email addresses only
- [ ] Test email delivery in staging environment first
- [ ] Configure email rate limits
- [ ] Monitor email bounce rates

### 10. Backup & Recovery
- [ ] Set up automated database backups
- [ ] Test backup restoration procedure
- [ ] Store backups in secure, encrypted location
- [ ] Document disaster recovery plan
- [ ] Keep backups for required retention period

## 🔍 SECURITY AUDIT FINDINGS

### CRITICAL Issues Fixed:
1. ✅ Removed default admin password from app_settings.py
2. ✅ Made admin credentials required in bootstrap script
3. ✅ Changed API_DOCS_ENABLED default to false
4. ✅ Changed RATE_LIMIT_FAIL_OPEN default to false
5. ✅ Changed TRUSTED_HOSTS default from "*" to empty (must be configured)
6. ✅ Added non-root user to all Dockerfiles
7. ✅ Created secure environment template

### CRITICAL Issues Requiring Manual Action:
1. ⚠️ **IMMEDIATELY REVOKE EXPOSED CREDENTIALS:**
   - AI API Key: `sk-tivgxlqgcfylrzayegecbsolxlonbhgbaghtwlapsrgkzouw`
   - Mailjet API Key: `e4f8b551af1da42bb653bb53d465f6af`
   - Mailjet API Secret: `8093674e95971090d0531c3d54821cea`
   
2. ⚠️ **DELETE CURRENT .env FILE** - It contains exposed secrets
3. ⚠️ **ROTATE ALL CREDENTIALS** - Generate new keys for all services
4. ⚠️ **DELETE seed_credentials.csv** - Contains demo passwords

## 📋 DEPLOYMENT STEPS

### Step 1: Clean Up Secrets
```bash
# Remove exposed .env file
rm .env

# Remove seed credentials
rm Backend/storage/seed_credentials.csv

# Verify .gitignore includes .env
grep "^\.env$" .gitignore || echo ".env" >> .gitignore
```

### Step 2: Generate New Credentials
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate DB_PASSWORD
openssl rand -base64 32

# Generate PGADMIN_PASSWORD
openssl rand -base64 24
```

### Step 3: Configure Environment
```bash
# Copy secure template
cp .env.secure.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.

# Set admin credentials as environment variables
export ADMIN_EMAIL="your-admin@domain.com"
export ADMIN_PASSWORD="YourStrongPassword123!"
```

### Step 4: Revoke Exposed API Keys
1. Log in to SiliconFlow and revoke: `sk-tivgxlqgcfylrzayegecbsolxlonbhgbaghtwlapsrgkzouw`
2. Log in to Mailjet and revoke:
   - API Key: `e4f8b551af1da42bb653bb53d465f6af`
   - API Secret: `8093674e95971090d0531c3d54821cea`
3. Generate new API keys for both services
4. Update .env with new keys

### Step 5: Deploy
```bash
# Build and start with production compose file
docker compose -f docker-compose.prod.yml up --build -d

# Verify all services are running
docker compose -f docker-compose.prod.yml ps

# Check logs for errors
docker compose -f docker-compose.prod.yml logs -f
```

## 🛡️ POST-DEPLOYMENT VERIFICATION

- [ ] Verify API docs are disabled (404 on /docs endpoint)
- [ ] Test rate limiting is working
- [ ] Verify CORS only allows your frontend domain
- [ ] Test admin login with new credentials
- [ ] Verify email delivery works
- [ ] Check all services are running as non-root
- [ ] Scan for exposed secrets: `git secrets --scan`
- [ ] Run security scan: `docker scan aura-backend:prod`

## 📞 INCIDENT RESPONSE

If credentials are compromised:
1. Immediately revoke all exposed API keys
2. Rotate SECRET_KEY and restart all services
3. Force password reset for all users
4. Review audit logs for suspicious activity
5. Update .env with new credentials
6. Redeploy application

## 📚 ADDITIONAL RESOURCES

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

---

**Last Updated:** $(date)
**Security Audit By:** Amazon Q Developer
**Status:** CRITICAL ISSUES IDENTIFIED - DO NOT DEPLOY WITHOUT FIXES
