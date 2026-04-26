# 🚀 Quick Start: Secure Your Aura Deployment

## ⏱️ 5-Minute Security Setup

Follow these steps to secure your Aura deployment before going to production.

---

## Step 1: Revoke Exposed Credentials (2 minutes)

### AI API Key
1. Go to your AI provider dashboard (SiliconFlow or similar)
2. Find API Keys section
3. **REVOKE**: `sk-tivgxlqgcfylrzayegecbsolxlonbhgbaghtwlapsrgkzouw`
4. Generate a new API key
5. Save it securely (you'll need it in Step 3)

### Mailjet Credentials
1. Go to https://app.mailjet.com/account/api_keys
2. **REVOKE** API Key: `e4f8b551af1da42bb653bb53d465f6af`
3. **REVOKE** API Secret: `8093674e95971090d0531c3d54821cea`
4. Generate new API key and secret
5. Save them securely (you'll need them in Step 3)

---

## Step 2: Run Security Cleanup (1 minute)

### On Windows:
```powershell
.\security-cleanup.ps1
```

### On Linux/Mac:
```bash
chmod +x security-cleanup.sh
./security-cleanup.sh
```

This script will:
- ✅ Backup and remove exposed `.env` file
- ✅ Remove demo credentials
- ✅ Create new `.env` from secure template
- ✅ Update `.gitignore`

---

## Step 3: Generate & Configure Credentials (2 minutes)

### Generate Strong Credentials

**On Windows PowerShell:**
```powershell
# Generate SECRET_KEY (64 chars)
$secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "SECRET_KEY=$secretKey"

# Generate DB_PASSWORD (32 chars)
$dbPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "DB_PASSWORD=$dbPassword"

# Generate PGADMIN_PASSWORD (24 chars)
$pgPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object {[char]$_})
Write-Host "PGADMIN_PASSWORD=$pgPassword"
```

**On Linux/Mac:**
```bash
# Generate SECRET_KEY
echo "SECRET_KEY=$(openssl rand -hex 32)"

# Generate DB_PASSWORD
echo "DB_PASSWORD=$(openssl rand -base64 32)"

# Generate PGADMIN_PASSWORD
echo "PGADMIN_PASSWORD=$(openssl rand -base64 24)"
```

### Update .env File

Open `.env` in your editor and replace these values:

```bash
# Core Authentication
SECRET_KEY=<paste generated SECRET_KEY>

# Database
DB_PASSWORD=<paste generated DB_PASSWORD>
DATABASE_URL=postgresql://aura_user:<DB_PASSWORD>@postgres:5432/aura_production
ASSISTANT_DB_URL=postgresql://aura_user:<DB_PASSWORD>@postgres:5432/ai_assistant

# AI Provider (from Step 1)
AI_API_KEY=<paste new AI API key>
AI_API_BASE=<your AI provider URL>
AI_MODEL=<your model name>

# Email (from Step 1)
MAILJET_API_KEY=<paste new Mailjet API key>
MAILJET_API_SECRET=<paste new Mailjet API secret>
EMAIL_SENDER_EMAIL=noreply@your-verified-domain.com

# pgAdmin
PGADMIN_PASSWORD=<paste generated PGADMIN_PASSWORD>

# Production URLs (use HTTPS!)
LOGIN_URL=https://your-frontend-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
BACKEND_ORIGIN=https://your-backend-domain.com
BACKEND_API_BASE_URL=https://your-backend-domain.com
ASSISTANT_ORIGIN=https://your-assistant-domain.com

# Security Settings (DO NOT CHANGE)
API_DOCS_ENABLED=false
RATE_LIMIT_FAIL_OPEN=false
TRUSTED_HOSTS=your-backend-domain.com,your-frontend-domain.com
```

### Set Admin Credentials

**On Windows PowerShell:**
```powershell
$env:ADMIN_EMAIL = "your-admin@domain.com"
$env:ADMIN_PASSWORD = "YourStrongPassword123!"
```

**On Linux/Mac:**
```bash
export ADMIN_EMAIL="your-admin@domain.com"
export ADMIN_PASSWORD="YourStrongPassword123!"
```

---

## ✅ Verification Checklist

Before deploying, verify:

- [ ] Revoked old AI API key
- [ ] Revoked old Mailjet credentials
- [ ] Generated new SECRET_KEY (64+ characters)
- [ ] Generated new DB_PASSWORD (32+ characters)
- [ ] Updated `.env` with all new credentials
- [ ] Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables
- [ ] Changed all URLs to use HTTPS (production)
- [ ] Verified `.env` is in `.gitignore`
- [ ] Deleted `Backend/storage/seed_credentials.csv`

---

## 🚀 Deploy

Once all steps are complete:

```bash
# Build and start production stack
docker compose -f docker-compose.prod.yml up --build -d

# Check status
docker compose -f docker-compose.prod.yml ps

# Follow logs
docker compose -f docker-compose.prod.yml logs -f
```

---

## 🔍 Post-Deployment Verification

After deployment, test:

1. **API Docs Disabled**
   ```bash
   curl https://your-backend-domain.com/docs
   # Should return 404
   ```

2. **CORS Working**
   ```bash
   curl -H "Origin: https://malicious-site.com" https://your-backend-domain.com/api/users
   # Should be blocked
   ```

3. **Rate Limiting Active**
   ```bash
   # Try 15 rapid login attempts
   # Should get 429 Too Many Requests after 10 attempts
   ```

4. **Admin Login**
   - Go to your frontend
   - Login with ADMIN_EMAIL and ADMIN_PASSWORD
   - Should work successfully

---

## 📚 Next Steps

For complete security hardening:

1. Review [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) - Complete checklist
2. Read [docs/SECURITY_HARDENING.md](docs/SECURITY_HARDENING.md) - Architecture guide
3. Set up monitoring and logging
4. Configure automated backups
5. Set up SSL/TLS certificates
6. Configure firewall rules

---

## 🆘 Troubleshooting

### "Bootstrap failed: admin credentials required"
- Make sure you set `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables
- Check they're exported in your current shell session

### "Database connection failed"
- Verify `DB_PASSWORD` in `.env` matches in both `DATABASE_URL` and `ASSISTANT_DB_URL`
- Check database container is running: `docker compose ps`

### "Email delivery failed"
- Verify Mailjet credentials are correct
- Check your domain is verified in Mailjet
- Ensure SPF, DKIM, DMARC records are configured

### "API docs still accessible"
- Check `API_DOCS_ENABLED=false` in `.env`
- Restart backend container: `docker compose restart backend`

---

## ⚠️ Important Reminders

1. **NEVER commit `.env` to git**
2. **Use HTTPS in production** (not HTTP)
3. **Rotate credentials regularly** (every 90 days)
4. **Monitor security logs** for suspicious activity
5. **Keep dependencies updated** (monthly)
6. **Test backups regularly** (weekly)

---

## 📞 Need Help?

- **Security Issues**: Review [SECURITY_ALERT.md](SECURITY_ALERT.md)
- **Deployment Issues**: Review [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)
- **Architecture Questions**: Review [docs/SECURITY_HARDENING.md](docs/SECURITY_HARDENING.md)

---

**Time to Complete**: ~5 minutes  
**Difficulty**: Easy  
**Priority**: 🔴 CRITICAL - Required before production deployment
