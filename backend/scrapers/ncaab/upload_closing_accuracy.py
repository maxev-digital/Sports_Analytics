#!/usr/bin/env python3
"""
Upload Closing Line Accuracy Analysis to Google Sheets
Shows how many games finished within 5/10/15/20+ points of closing
"""

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime

def upload_closing_accuracy():
    """Upload comprehensive closing line accuracy to Google Sheets"""

    print("="*70)
    print("UPLOADING CLOSING LINE ACCURACY TO GOOGLE SHEETS")
    print("="*70)

    # Load matched games
    matched_file = "backend/data/analysis/all_matched_games_20251011_113313.csv"
    df = pd.read_csv(matched_file)

    # Ensure Deviation and Abs_Deviation exist
    if 'Deviation' not in df.columns:
        df['Deviation'] = df['Actual_Total'] - df['Closing_Total']
    if 'Abs_Deviation' not in df.columns:
        df['Abs_Deviation'] = abs(df['Deviation'])

    print(f"\nLoaded {len(df)} matched games")

    # Setup Google Sheets
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    creds_file = r'C:\Users\nashr\Projects\10k Advertising Lead Generation Workflow\google_credentials.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)

    # Open or create spreadsheet
    try:
        spreadsheet = client.open("NCAA Basketball Closing Line Analysis")
        print(f"\nOpened existing spreadsheet: {spreadsheet.title}")
    except:
        spreadsheet = client.create("NCAA Basketball Closing Line Analysis")
        spreadsheet.share('nashr@10kadvertising.com', perm_type='user', role='writer')
        print(f"\nCreated new spreadsheet: {spreadsheet.title}")

    # WORKSHEET 1: Executive Summary
    print("\nCreating Executive Summary...")
    try:
        sheet = spreadsheet.worksheet("Closing Line Accuracy")
        spreadsheet.del_worksheet(sheet)
    except:
        pass

    summary_sheet = spreadsheet.add_worksheet(title="Closing Line Accuracy", rows=100, cols=10)

    summary_data = [
        ["NCAA BASKETBALL CLOSING LINE ACCURACY ANALYSIS"],
        [f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
        [""],
        ["DATASET OVERVIEW"],
        ["Total Matched Games", len(df)],
        ["Date Range", f"{df['Date'].min()} to {df['Date'].max()}"],
        ["Data Source", "Odds API Pro + ESPN"],
        [""],
        ["CLOSING LINE ACCURACY STATISTICS"],
        ["Mean Deviation", f"{df['Deviation'].mean():.2f} points"],
        ["Median Deviation", f"{df['Deviation'].median():.2f} points"],
        ["Mean Absolute Error", f"{df['Abs_Deviation'].mean():.2f} points"],
        ["Std Deviation", f"{df['Deviation'].std():.2f} points"],
        ["Min Deviation", f"{df['Deviation'].min():.1f} points"],
        ["Max Deviation", f"{df['Deviation'].max():.1f} points"],
        [""],
        ["ACCURACY BREAKDOWN"],
        ["Threshold", "Games Within", "Percentage"],
    ]

    # Add accuracy distribution
    for threshold in [5, 10, 15, 20, 25, 30]:
        count = (df['Abs_Deviation'] <= threshold).sum()
        pct = count / len(df) * 100
        summary_data.append([f"Within {threshold} points", count, f"{pct:.1f}%"])

    summary_data.extend([
        [""],
        ["GAMES EXCEEDING THRESHOLDS"],
        ["Threshold", "Games Exceeding", "Percentage"],
    ])

    for threshold in [5, 10, 15, 20, 25, 30]:
        count = (df['Abs_Deviation'] > threshold).sum()
        pct = count / len(df) * 100
        summary_data.append([f"Over {threshold} points", count, f"{pct:.1f}%"])

    summary_data.extend([
        [""],
        ["KEY INSIGHTS"],
        ["1. Closing lines are highly accurate"],
        [f"2. {(df['Abs_Deviation'] <= 10).sum()/len(df)*100:.1f}% of games finish within 10 points"],
        [f"3. {(df['Abs_Deviation'] <= 20).sum()/len(df)*100:.1f}% of games finish within 20 points"],
        [f"4. Only {(df['Abs_Deviation'] > 30).sum()} games ({(df['Abs_Deviation'] > 30).sum()/len(df)*100:.1f}%) exceeded 30 points"],
        [f"5. Mean absolute error of {df['Abs_Deviation'].mean():.2f} points shows market efficiency"],
    ])

    summary_sheet.update('A1', summary_data)
    print("   Added Executive Summary")

    # WORKSHEET 2: All Historical Games
    print("\nUploading all matched games...")
    try:
        sheet = spreadsheet.worksheet("All Games")
        spreadsheet.del_worksheet(sheet)
    except:
        pass

    games_sheet = spreadsheet.add_worksheet(title="All Games", rows=len(df)+1, cols=12)

    # Prepare data
    games_data = [['Date', 'Home Team', 'Away Team', 'Closing Total', '# Books',
                   'Actual Total', 'Deviation', 'Abs Deviation', 'Within 5?',
                   'Within 10?', 'Within 15?', 'Within 20?']]

    for _, row in df.iterrows():
        games_data.append([
            row['Date'],
            row['Home_Team'],
            row['Away_Team'],
            row['Closing_Total'],
            row['Num_Books'],
            row['Actual_Total'],
            f"{row['Deviation']:.1f}",
            f"{row['Abs_Deviation']:.1f}",
            'Yes' if row['Abs_Deviation'] <= 5 else 'No',
            'Yes' if row['Abs_Deviation'] <= 10 else 'No',
            'Yes' if row['Abs_Deviation'] <= 15 else 'No',
            'Yes' if row['Abs_Deviation'] <= 20 else 'No',
        ])

    games_sheet.update('A1', games_data)
    print(f"   Added {len(df)} games")

    # WORKSHEET 3: Extreme Deviations
    print("\nAdding extreme deviations...")
    try:
        sheet = spreadsheet.worksheet("Extreme Deviations")
        spreadsheet.del_worksheet(sheet)
    except:
        pass

    extreme_sheet = spreadsheet.add_worksheet(title="Extreme Deviations", rows=100, cols=8)

    # Top 50 most extreme deviations
    extreme_df = df.nlargest(50, 'Abs_Deviation')

    extreme_data = [['GAMES WITH LARGEST DEVIATIONS FROM CLOSING LINE'],
                    [''],
                    ['Rank', 'Date', 'Home Team', 'Away Team', 'Closing', 'Actual', 'Deviation', 'Abs Deviation']]

    for i, (_, row) in enumerate(extreme_df.iterrows(), 1):
        extreme_data.append([
            i,
            row['Date'],
            row['Home_Team'],
            row['Away_Team'],
            row['Closing_Total'],
            row['Actual_Total'],
            f"{row['Deviation']:.1f}",
            f"{row['Abs_Deviation']:.1f}",
        ])

    extreme_sheet.update('A1', extreme_data)
    print(f"   Added top 50 extreme deviations")

    # WORKSHEET 4: Monthly Breakdown
    print("\nAdding monthly breakdown...")
    try:
        sheet = spreadsheet.worksheet("Monthly Analysis")
        spreadsheet.del_worksheet(sheet)
    except:
        pass

    monthly_sheet = spreadsheet.add_worksheet(title="Monthly Analysis", rows=50, cols=10)

    # Group by month
    df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M').astype(str)
    monthly_stats = df.groupby('Month').agg({
        'Abs_Deviation': ['count', 'mean', 'median', 'std']
    }).round(2)

    monthly_data = [['MONTHLY CLOSING LINE ACCURACY'],
                    [''],
                    ['Month', 'Games', 'Mean Abs Error', 'Median Abs Error', 'Std Dev']]

    for month, row in monthly_stats.iterrows():
        monthly_data.append([
            month,
            int(row[('Abs_Deviation', 'count')]),
            f"{row[('Abs_Deviation', 'mean')]:.2f}",
            f"{row[('Abs_Deviation', 'median')]:.2f}",
            f"{row[('Abs_Deviation', 'std')]:.2f}",
        ])

    monthly_sheet.update('A1', monthly_data)
    print("   Added monthly analysis")

    print("\n" + "="*70)
    print("SUCCESS - Uploaded to Google Sheets")
    print("="*70)
    print(f"\nSpreadsheet: {spreadsheet.url}")
    print(f"\nWorksheets created:")
    print("   1. Closing Line Accuracy - Executive summary")
    print("   2. All Games - Complete dataset ({} games)".format(len(df)))
    print("   3. Extreme Deviations - Top 50 largest deviations")
    print("   4. Monthly Analysis - Accuracy by month")

    return spreadsheet.url


if __name__ == "__main__":
    import sys
    try:
        url = upload_closing_accuracy()
        print(f"\nView results: {url}")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
