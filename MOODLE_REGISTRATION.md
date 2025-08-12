# LTI 1.3 Setup Guide - Correct Registration Flow

## 🔄 **LTI 1.3 Registration Process**

In LTI 1.3, there's a specific flow where **Moodle provides values to your tool**, not the other way around.

 ### **Step-by-Step Registration Process:**

##📋 **Phase 1: Tool Information (What YOU provide to Moodle)**

When registering your tool in Moodle, you provide these **tool endpoints**:

| Field in Moodle | Your Value |
|------------------|------------|
| **Tool name** | `FastAPI LTI 1.3 Tool` |
| **Tool URL** | `http://localhost:8000/lti/launch` |
| **Initiate login URL** | `http://localhost:8000/lti/login` |
| **Redirection URI(s)** | `http://localhost:8000/lti/launch` |
| **Public keyset URL** | `http://localhost:8000/lti/jwks` |

## 📥 **Phase 2: Platform Information (What MOODLE provides to you)**

After registration, **Moodle will give you these values**:

| Moodle Provides | Example Value | Put in your .env file |
|-----------------|---------------|----------------------|
| **Client ID** | `Fx3VlteGd7` | `LTI_CLIENT_ID=Fx3VlteGd7` |
| **Platform ID (Issuer)** | `http://localhost:8080` | `LTI_PLATFORM_ISSUER=http://localhost:8080` |
| **Authentication URL** | `http://localhost:8080/mod/lti/auth.php` | `LTI_PLATFORM_AUTH_URL=...` |
| **Access token URL** | `http://localhost:8080/mod/lti/token.php` | `LTI_PLATFORM_TOKEN_URL=...` |
| **Public keyset URL** | `http://localhost:8080/mod/lti/certs.php` | `LTI_PLATFORM_JWKS_URL=...` |
| **Deployment ID** | `1` or `12345` | `LTI_DEPLOYMENT_ID=1` |

## 🔧 **Current Setup Status:**

### **✅ What's Ready (Your Tool):**
- ✅ FastAPI server running on `http://localhost:8000`
- ✅ Public keys available at `http://localhost:8000/lti/jwks`
- ✅ Login endpoint at `http://localhost:8000/lti/login`
- ✅ Launch endpoint at `http://localhost:8000/lti/launch`
- ✅ Tool configuration at `http://localhost:8000/lti/config`

### **⚠️ What You Need from Moodle:**
Your `.env` file currently has placeholder values that need to be replaced:

```bash
# UPDATE THESE with values from Moodle registration:
LTI_CLIENT_ID=CHANGE_ME_MOODLE_WILL_PROVIDE_THIS
LTI_DEPLOYMENT_ID=CHANGE_ME_MOODLE_WILL_PROVIDE_THIS
LTI_PLATFORM_ISSUER=CHANGE_ME_MOODLE_WILL_PROVIDE_THIS
LTI_PLATFORM_AUTH_URL=CHANGE_ME_MOODLE_WILL_PROVIDE_THIS
LTI_PLATFORM_TOKEN_URL=CHANGE_ME_MOODLE_WILL_PROVIDE_THIS
LTI_PLATFORM_JWKS_URL=CHANGE_ME_MOODLE_WILL_PROVIDE_THIS
```

## 📝 **Moodle Registration Steps:**

### **Step 1: Access Moodle as Administrator**
```
http://localhost:8080/admin
```

### **Step 2: Navigate to External Tools**
```
Site Administration 
→ Plugins 
→ Activity modules 
→ External tool 
→ Manage tools
```

### **Step 3: Add New Tool**
Click **"Configure a tool manually"** and select **LTI 1.3**

### **Step 4: Fill Tool Information**
```
Tool name: FastAPI LTI 1.3 Tool
Tool URL: http://localhost:8000/lti/launch
LTI version: 1.3
Initiate login URL: http://localhost:8000/lti/login
Redirection URI(s): http://localhost:8000/lti/launch
Public keyset URL: http://localhost:8000/lti/jwks
```

### **Step 5: Get Platform Information from Moodle**
After saving, Moodle will show you:
- **Client ID** (copy this)
- **Platform ID** (copy this)
- **Authentication request URL** (copy this)
- **Access token URL** (copy this)
- **Public keyset URL** (copy this)
- **Deployment ID** (copy this)

### **Step 6: Update Your .env File**
Replace the placeholder values with the real ones from Moodle.

## 🔍 **Example Real Configuration:**

After Moodle registration, your `.env` might look like:

```bash
# Real values from Moodle (example):
LTI_CLIENT_ID=Fx3VlteGd7w8K9mN2pQr
LTI_DEPLOYMENT_ID=12345
LTI_PLATFORM_ISSUER=http://localhost:8080
LTI_PLATFORM_AUTH_URL=http://localhost:8080/mod/lti/auth.php
LTI_PLATFORM_TOKEN_URL=http://localhost:8080/mod/lti/token.php
LTI_PLATFORM_JWKS_URL=http://localhost:8080/mod/lti/certs.php
```

## 🧪 **Testing the Integration:**

1. **Complete Moodle registration** and update your `.env`
2. **Restart your FastAPI server** to load new config
3. **Create a course** in Moodle
4. **Add External Tool activity** and select your tool
5. **Launch the tool** - should work without signature errors!

## 🔧 **Health Check After Configuration:**

After updating your `.env` with Moodle values:

```bash
curl http://localhost:8000/lti/health
```

Should show real configuration instead of placeholder values.

## 💡 **Key Points:**

- ✅ **You provide**: Tool URLs (launch, login, jwks, etc.)
- ✅ **Moodle provides**: Client ID, Platform issuer, deployment ID
- ✅ **Both exchange**: Public keys for JWT verification
- ✅ **No shared secrets**: Uses public/private key cryptography
- ✅ **No signature issues**: JWT tokens eliminate OAuth 1.0a problems

**The OAuth signature validation error you had with LTI 1.1 is completely eliminated in LTI 1.3!** 🎉
