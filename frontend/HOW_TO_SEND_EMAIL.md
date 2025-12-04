# How to Send the Beta Tester Email

## 📧 Quick Start

You have 3 options for sending the email to your beta testers:

---

## Option 1: Upload Files to Server (Recommended)

### Step 1: Upload Files to Your VPS

```bash
# Upload the ZIP file
scp "C:\Users\nashr\frontend\dist-electron\MAX-EV-SPORTS-Desktop-v1.0.0.zip" root@max-ev-sports.com:/var/www/downloads/

# Upload the logo (if you want it hosted)
scp "C:\Users\nashr\frontend\MAX-EV-SPORTS-Logo.png" root@max-ev-sports.com:/var/www/downloads/
```

### Step 2: Verify Download Links

Make sure these URLs work:
- `https://max-ev-sports.com/downloads/MAX-EV-SPORTS-Desktop-v1.0.0.zip`
- `https://max-ev-sports.com/logo2.png` (or upload to /downloads/)

### Step 3: Send HTML Email

1. Open your email client (Gmail, Outlook, etc.)
2. Open `C:\Users\nashr\frontend\BETA_TESTER_EMAIL.html` in a browser
3. Select all (Ctrl+A) and copy (Ctrl+C)
4. Paste into a new email (it will preserve formatting)
5. Update the logo URL if you hosted it differently
6. Send!

**Subject:** 🎉 You're In! MAX EV SPORTS Desktop - Beta Access

**BCC:** Add all your Elite subscriber emails

---

## Option 2: Use Email Service (Brevo, Mailchimp, etc.)

### For Brevo (Your CRM):

1. **Create New Campaign** in Brevo
2. **Use HTML Editor**
3. **Paste HTML** from `BETA_TESTER_EMAIL.html`
4. **Update Logo URL** to your hosted version
5. **Test Send** to yourself first
6. **Send to Elite Segment**

### Logo Hosting:
Upload logo to: `https://max-ev-sports.com/downloads/MAX-EV-SPORTS-Logo.png`
Then update the HTML:
```html
<img src="https://max-ev-sports.com/downloads/MAX-EV-SPORTS-Logo.png" alt="MAX EV SPORTS">
```

---

## Option 3: Gmail with Attachments

### If you can't host the files:

1. **Compress the ZIP** (it's already ~280MB, might be too large for email)
2. **Upload to Google Drive** or Dropbox instead
3. **Get shareable link**
4. **Update the download button** in the HTML:

```html
<a href="YOUR_GOOGLE_DRIVE_LINK_HERE">
    📥 Download Desktop Client
</a>
```

5. Send the email with logo attached

---

## 📋 Files You Need

### In `C:\Users\nashr\frontend\`:

1. **BETA_TESTER_EMAIL.html** - HTML email (use this for pretty emails)
2. **BETA_TESTER_EMAIL.txt** - Plain text version (fallback)
3. **MAX-EV-SPORTS-Logo.png** - Logo to attach/upload (209 KB)

### In `C:\Users\nashr\frontend\dist-electron\`:

4. **MAX-EV-SPORTS-Desktop-v1.0.0.zip** - The actual desktop app (~280 MB)

---

## 🎯 Example Email Setup (Gmail)

### Subject Line:
```
🎉 You're In! MAX EV SPORTS Desktop - Beta Access
```

### Recipients:
- **To:** Your personal email (for testing)
- **BCC:** All Elite subscribers (for actual send)

### Body:
1. Open `BETA_TESTER_EMAIL.html` in Chrome/Edge
2. Select all content (Ctrl+A)
3. Copy (Ctrl+C)
4. Paste into Gmail compose window (Ctrl+V)
5. Verify it looks good
6. Update any placeholder text
7. Send test to yourself first!

### Attachments:
- Attach `MAX-EV-SPORTS-Logo.png` if logo hosting doesn't work
- **DO NOT** attach the 280MB ZIP - use download link instead

---

## ✅ Pre-Send Checklist

Before sending to all testers:

- [ ] Uploaded ZIP file to server (or Google Drive)
- [ ] Tested download link works
- [ ] Uploaded logo to server (or will attach)
- [ ] Updated logo URL in HTML
- [ ] Sent test email to yourself
- [ ] Verified formatting looks good
- [ ] Checked all links work
- [ ] Ready to send!

---

## 🔗 Quick Command Reference

### Upload to VPS:
```bash
# ZIP file
scp "C:\Users\nashr\frontend\dist-electron\MAX-EV-SPORTS-Desktop-v1.0.0.zip" root@max-ev-sports.com:/var/www/downloads/

# Logo
scp "C:\Users\nashr\frontend\MAX-EV-SPORTS-Logo.png" root@max-ev-sports.com:/var/www/downloads/
```

### Make files publicly accessible:
```bash
ssh root@max-ev-sports.com
chmod 644 /var/www/downloads/MAX-EV-SPORTS-Desktop-v1.0.0.zip
chmod 644 /var/www/downloads/MAX-EV-SPORTS-Logo.png
```

### Test URLs:
- ZIP: `https://max-ev-sports.com/downloads/MAX-EV-SPORTS-Desktop-v1.0.0.zip`
- Logo: `https://max-ev-sports.com/downloads/MAX-EV-SPORTS-Logo.png`

---

## 💡 Pro Tips

1. **Test First:** Always send to yourself first to check formatting
2. **BCC for Privacy:** Use BCC for multiple recipients to protect privacy
3. **Timing:** Send during business hours for better open rates
4. **Follow Up:** Send reminder after 3-5 days if no response
5. **Track Opens:** Use Brevo to see who opened the email

---

## 📞 Support Email Setup

Make sure `support@max-ev-sports.com` is set up and monitored!

If you need to set up a support email:
1. Create email forwarding in your domain settings
2. Or set up a dedicated support inbox
3. Or use your personal email temporarily

---

## 🎨 Customization

Want to change the email design?

**Edit:** `BETA_TESTER_EMAIL.html`

**Key sections to update:**
- Download URL (line ~95)
- Support email (update all instances)
- Your branding colors
- Footer links

---

**Ready to send? Good luck with your beta test!** 🚀
