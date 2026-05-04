# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in HireMind, please follow these guidelines:

### Do Not
- ❌ Create a public GitHub issue
- ❌ Post the vulnerability on social media
- ❌ Share details without authorization

### Do
- ✅ Email security@hiremind.app with details
- ✅ Include steps to reproduce if possible
- ✅ Wait for confirmation before public disclosure

### Response Timeline
- **Initial Response**: Within 48 hours
- **Status Updates**: Every 7 days
- **Fix Release**: Within 30 days (high severity) or 90 days (normal)

## Security Best Practices

### For Users
1. **Keep dependencies updated** - Run `pip install --upgrade` regularly
2. **Use environment variables** - Never hardcode secrets
3. **Enable HTTPS** - Always use HTTPS in production
4. **Rotate credentials** - Change API keys and database passwords regularly
5. **Validate uploads** - Configure file upload restrictions

### For Developers
1. **Input validation** - Always validate user inputs
2. **SQL injection prevention** - Use parameterized queries
3. **CORS configuration** - Only allow trusted origins
4. **Rate limiting** - Implement rate limits on API endpoints
5. **Logging** - Log security events (without logging sensitive data)
6. **Updates** - Keep all dependencies current

### Known Security Measures
- JWT token-based authentication
- Password hashing with secure algorithms
- File upload validation
- API rate limiting
- CORS protection
- Input sanitization

## Security Advisories

For security advisories and updates, visit our [GitHub Security Page](https://github.com/yourusername/HireMind/security)

## Dependency Security

We use automated tools to check for vulnerabilities:
```bash
# Check dependencies
pip-audit  # For Python packages
npm audit  # For Node packages
```

## Responsible Disclosure

We appreciate your help in making HireMind secure. We follow responsible disclosure principles and will:
1. Acknowledge receipt of your report
2. Provide regular updates on progress
3. Credit you publicly if you wish (with your permission)
4. Work toward a coordinated fix

## Questions?

For security-related questions, contact: security@hiremind.app

---

Last Updated: April 2024
