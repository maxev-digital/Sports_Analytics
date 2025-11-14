#!/usr/bin/env python3
"""Check what password corresponds to the common hash"""
import hashlib

common_hash = "ffc121a2210958bf74e5a874668f3d978d24b6a8241496ccff3c0ea245e4f126"

# Test common passwords
passwords = [
    "password123",
    "Password123",
    "MaxEV2025!",
    "MaxEvSports!",
    "SportsBetting!",
    "LiveTrader!",
    "TerryMaxEV2025!",
    "admin123",
    "password",
    "Password",
    "test123",
    "Test123",
    "MaxEV123",
    "SportTrader",
    "SportTrader!",
    "SportTrader1",
    "SportTrader2",
    "SportTrader3",
    "SportTrader4",
]

print(f"Looking for password matching hash: {common_hash}")
print()

for pw in passwords:
    pw_hash = hashlib.sha256(pw.encode()).hexdigest()
    if pw_hash == common_hash:
        print(f"MATCH FOUND: '{pw}'")
        print(f"Hash: {pw_hash}")
        break
    else:
        print(f"'{pw}' -> {pw_hash[:20]}... (no match)")
else:
    print("\nNo match found in common passwords list")
