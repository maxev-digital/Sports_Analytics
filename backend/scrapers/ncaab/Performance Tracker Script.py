import pandas as pd
from io import StringIO

# Daily Performance Data (as CSV string)
daily_csv = """
Date,Wagers,Wins,Losses,Win%,Units,Avg Unit,Avg Price,W/L,ROI%
MON 9/1,14,8,6,57.1,3.5,0.25,1.62,0.34,9.64%
TUE 9/2,14,8,6,57.1,3.75,0.27,1.05,0.01,2.68%
WED 9/3,12,6,6,50.0,3.0,0.25,2.05,0.01,7.89%
THU 9/4,27,13,14,48.1,7.1,0.26,2.00,0.27,3.73%
FRI 9/5,67,40,27,59.7,14.8,0.27,2.04,2.03,15.95%
SAT 9/6,28,12,16,42.9,6.5,0.25,2.18,0.05,6.0%
SUN 9/7,14,7,7,50.0,2.75,0.25,1.00,0.51,2.75%
MON 9/8,19,9,7,47.4,3.75,0.25,1.03,0.31,3.47%
TUE 9/9,12,5,7,41.7,2.25,0.25,1.01,-0.40,-12.31%
WED 9/10,15,4,11,26.7,3.55,0.24,1.94,-1.71,-48.10%
THU 9/11,24,14,10,58.3,5.25,0.26,1.89,0.53,40.84%
FRI 9/12,67,35,32,52.2,17.34,0.26,2.10,0.06,6.14%
SAT 9/13,68,40,28,58.8,17.88,0.26,1.92,0.42,10.10%
SUN 9/14,14,6,8,42.9,3.5,0.25,2.34,-1.54,-20.08%
MON 9/15,28,12,16,42.9,6.0,0.25,2.18,0.04,0.08%
TUE 9/16,12,9,3,75.0,3.0,0.25,2.00,0.51,5.17%
WED 9/17,16,7,9,43.8,4.0,0.25,2.00,-0.82,-12.55%
THU 9/18,67,42,25,62.7,13.38,0.28,2.03,0.22,24.29%
FRI 9/19,10,5,5,50.0,2.5,0.25,2.04,0.05,5.0%
SAT 9/20,67,42,25,62.7,13.38,0.28,2.03,0.22,24.29%
SUN 9/21,45,29,16,64.4,12.38,0.28,2.04,0.32,24.41%
MON 9/22,10,5,5,50.0,2.5,0.25,2.32,0.08,20.00%
TUE 9/23,28,20,8,71.4,7.25,0.26,2.02,0.34,48.07%
WED 9/24,0,0,0,0.0,0.0,0.0,0.0,0.0,0.0%
THU 9/25,12,3,9,25.0,0.06,0.25,3.25,-0.82,-27.65%
FRI 9/26,25,8,17,32.0,1.5,0.25,1.89,-0.48,-38.08%
SAT 9/27,67,34,33,50.7,16.96,0.25,1.82,1.82,10.72%
SUN 9/28,73,29,44,39.7,16.96,0.27,1.82,-0.79,-10.38%
MON 9/29,15,9,6,60.0,3.55,0.24,2.08,0.09,30.63%
TUE 9/30,16,10,6,62.5,4.25,0.27,1.62,1.04,24.47%
TOTAL,881,463,418,52.6%,227.02,0.26,2.12,18.20,7.93%
"""

# Monthly Summary by Sport Data (as CSV string)
summary_csv = """
Sport,Wagers,Wins,Win%,Units,Avg Price,W/L,ROI%
PACE,237,120,50.6%,64.30,1.34,4.18,4.89%
TAW,171,90,52.6%,42.18,2.15,3.31,12.16%
GOSU,147,71,48.3%,37.51,2.05,-1.54,-4.12%
GEUTEN,128,69,53.9%,32.05,2.10,4.16,12.73%
STEW,81,44,54.3%,19.96,2.28,4.45,22.28%
HAWKEYE,122,68,55.7%,32.75,1.87,3.53,10.78%
MARSH,67,35,52.2%,17.50,2.07,1.39,7.89%
NHL,37,19,51.4%,17.50,2.07,1.39,7.89%
EURO PUCK,24,13,54.2%,6.00,2.17,1.08,17.78%
NFL,350,175,50.0%,62.09,2.02,2.64,5.09%
NFBRE,294,150,51.0%,74.64,2.01,4.38,5.99%
NCAF,34,18,52.9%,8.00,1.98,-0.09,-1.09%
NBA,89,55,61.8%,23.00,1.98,5.63,24.59%
WNBA,4,3,75.0%,1.00,1.95,0.49,48.39%
NCAA,2,2,100.0%,1.00,2.47,0.73,146.5%
TENNIS,1,0,0.0%,0.25,2.30,-0.25,-100.0%
SOCCER,1,1,100.0%,0.26,2.30,0.33,130.0%
UFC,14,4,28.6%,3.24,2.30,-0.24,-7.09%
GOLF,3,2,66.7%,1.50,1.83,0.89,59.09%
MIDDLES,3,2,66.7%,1.50,1.83,0.89,59.09%
"""

# Load data into DataFrames
daily_df = pd.read_csv(StringIO(daily_csv))
summary_df = pd.read_csv(StringIO(summary_csv))

# Clean percentages
daily_df['Win%'] = daily_df['Win%'].str.rstrip('%').astype(float)
daily_df['ROI%'] = daily_df['ROI%'].str.rstrip('%').astype(float)
summary_df['Win%'] = summary_df['Win%'].str.rstrip('%').astype(float)
summary_df['ROI%'] = summary_df['ROI%'].str.rstrip('%').astype(float)

# Compute Cumulative Units for daily
daily_df['Cumulative Units'] = daily_df['Units'].cumsum()

# Export to CSV files
daily_df.to_csv('daily_performance_sept2025.csv', index=False)
summary_df.to_csv('monthly_summary_sept2025.csv', index=False)

print("CSV files have been created: 'daily_performance_sept2025.csv' and 'monthly_summary_sept2025.csv'. ")
print("To use in Google Sheets:")
print("- Open Google Sheets.")
print("- Go to File > Import > Upload.")
print("- Select the CSV files to import into separate sheets.")