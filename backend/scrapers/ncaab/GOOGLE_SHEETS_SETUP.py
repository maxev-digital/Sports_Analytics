"""
NCAA Basketball Google Sheets Setup Guide
Using Your Existing Service Account
"""

# ============================================================================
# STEP 1: FIND YOUR SERVICE ACCOUNT EMAIL
# ============================================================================

# Your service account email is in your existing credentials file.
# Let's find it:

"""
1. Open this file in a text editor:
   C:\Users\nashr\google_sheets\credentials\service-account-key.json

2. Look for the line that says "client_email"
   It will look like: "your-service-account@project-name.iam.gserviceaccount.com"

3. Copy this email address - you'll need it in Step 2
"""

# ============================================================================
# STEP 2: CREATE NEW NCAA BASKETBALL GOOGLE SHEET
# ============================================================================

"""
1. Go to: https://sheets.google.com

2. Click: "+ Blank" to create a new spreadsheet

3. Rename it to: "NCAA Basketball Betting Model"

4. In the sheet, add these column headers in Row 1:
   A: Date
   B: Time
   C: Home_Team
   D: Away_Team
   E: Home_Tempo
   F: Away_Tempo
   G: Expected_Pace
   H: Home_OffEff
   I: Home_DefEff
   J: Away_OffEff
   K: Away_DefEff
   L: Home_Points
   M: Away_Points
   N: Model_Total
   O: Market_Total
   P: Edge
   Q: Recommendation
   R: Confidence
   S: Bet?

5. Format the header row (optional but recommended):
   - Bold text
   - Light gray background
   - Freeze row (View → Freeze → 1 row)
"""

# ============================================================================
# STEP 3: SHARE SHEET WITH SERVICE ACCOUNT
# ============================================================================

"""
1. In your Google Sheet, click the "Share" button (top right)

2. In the "Add people and groups" field, paste your service account email
   (from Step 1)

3. Set permission to: "Editor"

4. IMPORTANT: Uncheck "Notify people" (the service account is a robot, not a person)

5. Click "Share"

6. You should see the service account email in the list of people with access
"""

# ============================================================================
# STEP 4: GET YOUR SHEET ID
# ============================================================================

"""
1. Look at the URL of your Google Sheet. It looks like:
   https://docs.google.com/spreadsheets/d/1ABC123xyz789_EXAMPLE_ID/edit

2. Copy the long string between "/d/" and "/edit"
   Example: 1ABC123xyz789_EXAMPLE_ID

3. This is your SHEET ID - save it for Step 5
"""

# ============================================================================
# STEP 5: CONFIGURE THE NCAA BASKETBALL MODEL
# ============================================================================

"""
1. Open this file in a text editor:
   C:\Users\nashr\config.py

2. Replace this line:
   GOOGLE_SHEET_ID = "YOUR_SHEET_ID_HERE"
   
   With your actual Sheet ID:
   GOOGLE_SHEET_ID = "1ABC123xyz789_EXAMPLE_ID"

3. Save the file

4. Copy config.py to your project:
   copy C:\Users\nashr\config.py C:\Users\nashr\backend\config.py
"""

# ============================================================================
# STEP 6: VERIFY CREDENTIALS FILE EXISTS
# ============================================================================

"""
Make sure this file exists:
C:\Users\nashr\google_sheets\credentials\service-account-key.json

If it doesn't exist, check these locations:
- Your NBA model folder
- Your NFL model folder

Copy it to the NCAA Basketball project location.
"""

# ============================================================================
# STEP 7: TEST THE SETUP
# ============================================================================

"""
After completing steps 1-6, test the setup:

cd C:\Users\nashr
python run_ncaab_predictions.py

If everything is configured correctly, you'll see:
✅ Uploaded to Google Sheets
"""

# ============================================================================
# QUICK TROUBLESHOOTING
# ============================================================================

"""
ERROR: "Insufficient Permission"
→ Make sure you shared the sheet with the service account email as Editor

ERROR: "Spreadsheet not found"
→ Check that you copied the correct Sheet ID

ERROR: "Credentials file not found"
→ Verify the path in config.py matches where your credentials file is located

ERROR: "API has not been enabled"
→ Your existing service account should already have Sheets API enabled from NBA/NFL setup
"""

# ============================================================================
# SUMMARY
# ============================================================================

print("""
✅ YOU'RE REUSING YOUR EXISTING SERVICE ACCOUNT

Benefits:
- No need to create a new Google Cloud project
- Same credentials work for NFL, NBA, and NCAA Basketball sheets
- One service account can access unlimited sheets

What you did:
1. Found your service account email (in credentials file)
2. Created new NCAA Basketball sheet
3. Shared it with service account (Editor access)
4. Got the Sheet ID from URL
5. Updated config.py with Sheet ID
6. Ready to run predictions!
""")
