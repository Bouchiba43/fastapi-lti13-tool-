# FastAPI LTI 1.3 Tool for Moodle

This is a modern Learning Tools Interoperability (LTI) 1.3 external tool built with FastAPI, designed for seamless integration with Moodle and other LMS platforms. It uses JWT and public/private key cryptography for secure launches—no more OAuth signature errors!


## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- Moodle instance with LTI 1.3 external tool support

### Local Development

1. **Clone and navigate to the project:**
   ```bash
   git clone <your-repo-url>
   cd lti
   ```
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   Edit `.env` with values from Moodle registration (see below).
5. **Run the application:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```



## 🔄 LTI 1.3 Registration Flow

### Phase 1: What YOU Provide to Moodle

Register your tool in Moodle with these endpoints:

| Field in Moodle         | Your Value                          |
|------------------------|-------------------------------------|
| Tool name              | FastAPI LTI 1.3 Tool                |
| Tool URL               | http://localhost:8000/lti/launch    |
| Initiate login URL     | http://localhost:8000/lti/login     |
| Redirection URI(s)     | http://localhost:8000/lti/launch    |
| Public keyset URL      | http://localhost:8000/lti/jwks      |


### Phase 2: What Moodle Provides to YOU

After registration, Moodle will give you:

| Moodle Provides         | Example Value                      | .env Variable                  |
|------------------------|------------------------------------|-------------------------------|
| Client ID              | Jwe2k2qBSQKV7v7                    | LTI_CLIENT_ID=Jwe2k2qBSQKV7v7 |
| Platform ID (Issuer)   | http://localhost:8080              | LTI_PLATFORM_ISSUER=...       |
| Authentication URL     | http://localhost:8080/mod/lti/auth.php | LTI_PLATFORM_AUTH_URL=...    |
| Access token URL       | http://localhost:8080/mod/lti/token.php | LTI_PLATFORM_TOKEN_URL=...   |
| Public keyset URL      | http://localhost:8080/mod/lti/certs.php | LTI_PLATFORM_JWKS_URL=...   |
| Deployment ID          | 2                                  | LTI_DEPLOYMENT_ID=2           |


## 📝 Example .env Configuration

After Moodle registration, your `.env` should look like:

```dotenv
LTI_CLIENT_ID=Jwe2k2qBSQKV7v7
LTI_DEPLOYMENT_ID=2
LTI_TOOL_URL=http://localhost:8000
LTI_PLATFORM_ISSUER=http://localhost:8080
LTI_PLATFORM_AUTH_URL=http://localhost:8080/mod/lti/auth.php
LTI_PLATFORM_TOKEN_URL=http://localhost:8080/mod/lti/token.php
LTI_PLATFORM_JWKS_URL=http://localhost:8080/mod/lti/certs.php
LTI_PRIVATE_KEY_PATH=keys/private.pem
LTI_PUBLIC_KEY_PATH=keys/public.pem
LTI_KEY_ID=lti-key-1
SECRET_KEY=dev-secret-key-for-jwt-tokens-change-in-production-12345
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
HOST=0.0.0.0
PORT=8000
DEBUG=true
RELOAD=true
```


## 📝 Moodle Registration Steps

1. **Access Moodle as Administrator**
   - Go to `http://localhost:8080/admin`
2. **Navigate to External Tools**
   - Site Administration → Plugins → Activity modules → External tool → Manage tools
3. **Add New Tool**
   - Click "Configure a tool manually" and select LTI 1.3
4. **Fill Tool Information**
   - Use the endpoints above
5. **Copy Platform Info from Moodle**
   - After saving, Moodle will show you the values for your `.env`
6. **Update `.env` and Restart Server**

#### Example Tool Information
```
Tool name: FastAPI LTI 1.3 Tool
Tool URL: http://localhost:8000/lti/launch
LTI version: 1.3
Initiate login URL: http://localhost:8000/lti/login
Redirection URI(s): http://localhost:8000/lti/launch
Public keyset URL: http://localhost:8000/lti/jwks
```

#### Example Platform Information from Moodle
- **Client ID** (copy this)
- **Platform ID** (copy this)
- **Authentication request URL** (copy this)
- **Access token URL** (copy this)
- **Public keyset URL** (copy this)
- **Deployment ID** (copy this)

#### Update Your .env File
Replace the placeholder values with the real ones from Moodle.


## 🧪 Testing the Integration

1. Complete Moodle registration and update your `.env`
2. Restart your FastAPI server
3. Create a course in Moodle
4. Add External Tool activity and select your tool
5. Launch the tool—should work without signature errors!


## 🔧 Health Check

After updating your `.env`:

```bash
curl http://localhost:8000/health
```
Should show "healthy" status and your real configuration.


## 💡 Key Points

- ✅ You provide: Tool URLs (launch, login, jwks, etc.)
- ✅ Moodle provides: Client ID, Platform issuer, deployment ID
- ✅ Both exchange: Public keys for JWT verification
- ✅ No shared secrets: Uses public/private key cryptography
- ✅ No signature issues: JWT tokens eliminate OAuth 1.0a problems

**The OAuth signature validation error you had with LTI 1.1 is completely eliminated in LTI 1.3! 🎉**


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.


## 🆘 Support

For support and questions:

1. Check this README for common solutions
2. Review the troubleshooting section
3. Check application logs
4. Open an issue on the repository


## 🔗 Resources

- [LTI 1.3 Specification](https://www.imsglobal.org/spec/lti/v1p3/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Moodle LTI Documentation](https://docs.moodle.org/en/External_tool)
