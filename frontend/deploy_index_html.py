#!/usr/bin/env python3
"""Deploy ONLY index.html to fix reference"""
import paramiko

VPS_HOST = "148.230.87.135"
VPS_USER = "root"
VPS_PASSWORD = "W7MeAe;IqDOBBCz8cg&u"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD)
sftp = ssh.open_sftp()

print("Uploading index.html...")
sftp.put("dist/index.html", "/root/sporttrader/frontend/dist/index.html")
print("[OK] index.html uploaded")

# Verify
stdin, stdout, stderr = ssh.exec_command("cat /root/sporttrader/frontend/dist/index.html | grep -o 'index-[^.]*\.js'")
result = stdout.read().decode().strip()
print(f"VPS index.html now references: {result}")

sftp.close()
ssh.close()
