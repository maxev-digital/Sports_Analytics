#!/usr/bin/env python3
"""Verify what's actually deployed on VPS"""
import paramiko
import os
from pathlib import Path

VPS_HOST = "148.230.87.135"
VPS_USER = "root"
VPS_PASSWORD = "W7MeAe;IqDOBBCz8cg&u"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD)

# Check what index-*.js file is on VPS
stdin, stdout, stderr = ssh.exec_command("ls -lh /root/sporttrader/frontend/dist/assets/index-*.js")
vps_files = stdout.read().decode()
print("VPS Files:")
print(vps_files)
print()

# Check local files
local_files = os.popen("ls -lh dist/assets/index-*.js").read()
print("Local Files:")
print(local_files)
print()

# Get file sizes to compare
stdin, stdout, stderr = ssh.exec_command("stat -c '%s %n' /root/sporttrader/frontend/dist/assets/index-*.js")
vps_size = stdout.read().decode().strip()
local_size = os.popen("stat -c '%s %n' dist/assets/index-*.js 2>/dev/null || stat -f '%z %N' dist/assets/index-*.js").read().strip()

print(f"VPS size: {vps_size}")
print(f"Local size: {local_size}")
print()

if vps_size.split()[0] != local_size.split()[0]:
    print("[ERROR] Files are DIFFERENT - deployment may have failed!")
    print("Recommended: Re-run deployment")
else:
    print("[OK] Files match - deployment successful")

ssh.close()
