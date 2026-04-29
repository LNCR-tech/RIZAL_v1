# 🔐 Aura Security Hardening Guide

## Executive Summary

This document outlines the security measures implemented in Aura and provides guidance for secure deployment and operation.

## Security Architecture

### 1. Authentication & Authorization

#### JWT Token Security
- **Algorithm**: HS256 (configurable to RS256 with public key)
- **Token Expiration**: 30 minutes (configurable)
- **Session Management**: Database-backed session validation
- **Refresh Tokens**: Supported with "remember me" functionality

#### Password Security
- **Hashing**: bcrypt with automatic salt generation
- **Minimum Requirements**: Enforced at application level
- **Temporary Passwords**: Force password change on first login
- **Password Reset**: Admin-approved workflow for privileged accounts

#### Multi-Factor Authentication
- **Face Verification**: Optional biometric MFA for privileged operations
- **Liveness Detection**: Anti-spoofing with MiniFASNetV2 ONNX model
- **Threshold Configuration**: Separate thresholds for single/group/MFA scenarios

### 2. Rate Limiting

#### Implemented Rate Limits
- **Login Attempts**: 10 attempts per 5 minutes per IP+email
- **Password Reset**: 5 attempts per 5 minutes per IP+email
- **Authenticated Mutations**: 120 requests per minute per user
- **Face Recognition**: 20 requests per minute per user
- **Public Endpoints**: 30 requests per minute per IP

#### Configuration
```python
RATE_LIMIT_ENABLED=true
RATE_LIMIT_FAIL_OPEN=false  # Deny on rate limit errors (secure default)
```

### 3. Input Validation & Sanitization

#### Request Body Size Limits
- **Default**: 8 MB maximum request body
- **Face Images**: 5 MB maximum per image
- **File Uploads**: 50 MB maximum for Excel imports

#### SQL Injection Prevention
- **ORM**: SQLAlchemy with parameterized queries
- **No Raw SQL**: All queries use ORM or prepared statements

#### XSS Prevention
- **Output Encoding**: Automatic in FastAPI/Pydantic
- **Content Security Policy**: Should be configured at reverse proxy

### 4. CORS & Host Validation

#### CORS Configuration
```python
# Production - restrict to your domain only
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

# Development - localhost only
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### Trusted Hosts
```python
# Production - specify exact domains
TRUSTED_HOSTS=your-backend-domain.com,your-frontend-domain.com

# Development - allow all (not recommended for production)
TRUSTED_HOSTS=*
```

### 5. API Security

#### API Documentation
- **Production**: Disabled by default (`API_DOCS_ENABLED=false`)
- **Development**: Enabled for testing
- **Endpoints**: `/docs`, `/redoc`, `/openapi.json`

#### Authentication Middleware
- **OAuth2 Bearer Tokens**: Required for all protected endpoints
- **Session Validation**: Database check on every request
- **Account State Validation**: Active status, role assignment, school status

### 6. Database Security

#### Connection Security
- **Connection Pooling**: Configured with timeouts and limits
- **Pool Size**: 10 connections (configurable)
- **Max Overflow**: 10 additional connections
- **Pool Timeout**: 15 seconds
- **Pool Recycle**: 30 minutes

#### Credentials Management
```bash
# Generate strong database password
openssl rand -base64 32

# Use in DATABASE_URL
DATABASE_URL=postgresql://aura_user:STRONG_PASSWORD@db:5432/aura_production
```

#### Data Isolation
- **Multi-tenancy**: School-scoped data isolation
- **Row-Level Security**: Enforced at application layer
- **Audit Logging**: All sensitive operations logged

### 7. Container Security

#### Non-Root Users
All containers run as non-root users:
```dockerfile
RUN useradd --create-home --no-log-init appuser
USER appuser
```

#### Image Security
- **Base Images**: Official Python/Node/Nginx images
- **Minimal Layers**: Reduced attack surface
- **No Secrets in Images**: All secrets via environment variables
- **Regular Updates**: Keep base images updated

#### Network Isolation
```yaml
# Internal services not exposed
services:
  postgres:
    # No ports exposed to host
  redis:
    # No ports exposed to host
```

### 8. File Upload Security

#### Validation
- **File Type**: Whitelist of allowed extensions
- **File Size**: Enforced limits per upload type
- **Content Validation**: Excel files validated before processing
- **Virus Scanning**: Recommended for production (not included)

#### Storage
- **Isolated Directories**: Separate storage per file type
- **No Execution**: Storage directories not in execution path
- **Access Control**: Served through application, not direct access

### 9. Email Security

#### Transport Security
- **TLS/STARTTLS**: Supported for SMTP
- **API Transport**: Mailjet API with HTTPS
- **SPF/DKIM/DMARC**: Required for production domains

#### Content Security
- **Template Validation**: All emails use validated templates
- **No User HTML**: User input sanitized before email inclusion
- **Rate Limiting**: Prevent email bombing

### 10. Logging & Monitoring

#### Security Events Logged
- Login attempts (success and failure)
- Password changes
- Password reset requests
- Face verification attempts
- Rate limit violations
- Account state changes

#### Audit Trail
- **User Actions**: All mutations logged with user context
- **IP Addresses**: Captured for security events
- **Timestamps**: UTC timestamps for all events
- **Retention**: Configure based on compliance requirements

## Deployment Security Checklist

### Pre-Deployment

- [ ] Review and complete `SECURITY_CHECKLIST.md`
- [ ] Run `security-cleanup.sh` to remove exposed credentials
- [ ] Generate all new credentials (SECRET_KEY, DB_PASSWORD, etc.)
- [ ] Revoke any exposed API keys
- [ ] Configure `.env` with production values
- [ ] Set `API_DOCS_ENABLED=false`
- [ ] Set `RATE_LIMIT_FAIL_OPEN=false`
- [ ] Configure `TRUSTED_HOSTS` with actual domains
- [ ] Configure `CORS_ALLOWED_ORIGINS` with frontend domain only

### Infrastructure

- [ ] Use HTTPS/TLS for all public endpoints
- [ ] Configure reverse proxy (nginx/traefik) with SSL
- [ ] Restrict database access (no public exposure)
- [ ] Restrict Redis access (no public exposure)
- [ ] Configure firewall (allow only 80/443 publicly)
- [ ] Set up AWS Security Groups with minimal ports
- [ ] Enable VPC for database isolation

### Application

- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Set strong database password (32+ characters)
- [ ] Set strong admin password (12+ characters, mixed case, numbers, symbols)
- [ ] Remove or secure pgAdmin (use SSH tunnel or VPN)
- [ ] Configure email with verified domain
- [ ] Enable rate limiting
- [ ] Configure trusted hosts (no wildcards)
- [ ] Test authentication and authorization

### Monitoring

- [ ] Set up centralized logging
- [ ] Configure security event alerts
- [ ] Monitor failed login attempts
- [ ] Monitor rate limit violations
- [ ] Set up uptime monitoring
- [ ] Configure backup and recovery

## Security Incident Response

### If Credentials Are Compromised

1. **Immediate Actions**
   - Revoke compromised API keys immediately
   - Rotate SECRET_KEY
   - Force logout all users (invalidate all sessions)
   - Change database password
   - Restart all services

2. **Investigation**
   - Review audit logs for suspicious activity
   - Check for unauthorized access
   - Identify scope of compromise
   - Document timeline of events

3. **Recovery**
   - Update all credentials
   - Redeploy application
   - Force password reset for affected users
   - Notify affected parties if required

4. **Prevention**
   - Review how credentials were exposed
   - Implement additional controls
   - Update security procedures
   - Train team on security best practices

## Security Best Practices

### Development

1. **Never commit secrets to git**
   - Use `.env` files (in `.gitignore`)
   - Use environment variables
   - Use secret management tools (AWS Secrets Manager, HashiCorp Vault)

2. **Code review for security**
   - Review authentication/authorization logic
   - Check for SQL injection vulnerabilities
   - Verify input validation
   - Check for hardcoded credentials

3. **Dependency management**
   - Keep dependencies updated
   - Review security advisories
   - Use `pip-audit` or `safety` for Python
   - Use `npm audit` for Node.js

### Operations

1. **Regular updates**
   - Update base images monthly
   - Apply security patches promptly
   - Update dependencies regularly

2. **Backup and recovery**
   - Automated daily backups
   - Test restoration procedures
   - Encrypt backups
   - Store backups securely

3. **Access control**
   - Principle of least privilege
   - Regular access reviews
   - Strong password policies
   - Multi-factor authentication for admin access

## Compliance Considerations

### Data Protection
- **GDPR**: User data rights, consent, data minimization
- **CCPA**: California consumer privacy rights
- **FERPA**: Student education records (if applicable)

### Security Standards
- **OWASP Top 10**: Address common web vulnerabilities
- **CIS Benchmarks**: Follow security configuration guidelines
- **SOC 2**: Security, availability, confidentiality controls

## Security Contact

For security issues or questions:
- **Email**: security@your-domain.com
- **Response Time**: 24 hours for critical issues
- **Disclosure Policy**: Responsible disclosure encouraged

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Next Review**: Quarterly or after significant changes
