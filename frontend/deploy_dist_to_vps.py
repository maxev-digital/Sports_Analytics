#!/usr/bin/env python3
"""SURGICAL DEPLOYMENT - Upload dist/ to VPS only"""
import paramiko
import os
from pathlib import Path

VPS_HOST = "148.230.87.135"
VPS_USER = "root"
VPS_PASSWORD = "W7MeAe;IqDOBBCz8cg&u"
VPS_DIST = "/root/sporttrader/frontend/dist"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD)
sftp = ssh.open_sftp()

print("=" * 50)
print("SURGICAL FRONTEND DEPLOYMENT")
print("=" * 50)
print()

# Upload dist directory recursively
dist_path = Path("dist")
uploaded_count = 0

def upload_directory(local_dir, remote_dir):
    global uploaded_count
    try:
        sftp.stat(remote_dir)
    except:
        sftp.mkdir(remote_dir)

    for item in local_dir.iterdir():
        local_path = item
        remote_path = f"{remote_dir}/{item.name}"

        if item.is_dir():
            upload_directory(local_path, remote_path)
        else:
            sftp.put(str(local_path), remote_path)
            uploaded_count += 1
            if uploaded_count % 10 == 0:
                print(f"Uploaded {uploaded_count} files...")

print("Uploading dist/ to VPS...")
upload_directory(dist_path, VPS_DIST)

sftp.close()
ssh.close()

print()
print(f"[OK] Uploaded {uploaded_count} files to {VPS_DIST}")
print()
print("=" * 50)
print("DEPLOYMENT COMPLETE!")
print("=" * 50)
print()
print("Test at: https://max-ev-sports.com/props")
