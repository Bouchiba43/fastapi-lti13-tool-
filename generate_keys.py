#!/usr/bin/env python3
# generate_keys.py - Generate RSA key pair for LTI 1.3

import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_rsa_key_pair():
    """Generate RSA key pair for LTI 1.3 JWT signing"""
    
    keys_dir = Path("keys")
    keys_dir.mkdir(exist_ok=True)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open(keys_dir / "private.pem", "wb") as f:
        f.write(private_pem)
    
    with open(keys_dir / "public.pem", "wb") as f:
        f.write(public_pem)
    
    print("✅ RSA key pair generated successfully!")
    print(f"   Private key: {keys_dir / 'private.pem'}")
    print(f"   Public key: {keys_dir / 'public.pem'}")
    print("\n🔒 Keep the private key secure and never share it!")
    print("📤 The public key will be shared via the JWKS endpoint")

if __name__ == "__main__":
    generate_rsa_key_pair()
