"""
Script to add 15 new stats to NCAAF scraper
"""

# Read the current file
with open('scrapers/teamrankings_ncaaf_scraper.py', 'r') as f:
    content = f.read()

# Define the 15 new stats to scrape
new_scraping_code = """        takeaways = self.scrape_stat_page('takeaways-per-game')
        time.sleep(1)

        # NEW: Additional advanced stats (matching NFL)
        yards_per_play = self.scrape_stat_page('yards-per-play')
        time.sleep(1)

        opp_yards_per_play = self.scrape_stat_page('opponent-yards-per-play')
        time.sleep(1)

        completion_pct = self.scrape_stat_page('completion-percentage')
        time.sleep(1)

        opp_completion_pct = self.scrape_stat_page('opponent-completion-percentage')
        time.sleep(1)

        fourth_down_pct = self.scrape_stat_page('fourth-down-conversion-pct')
        time.sleep(1)

        interceptions = self.scrape_stat_page('interceptions-per-game')
        time.sleep(1)

        fumbles_lost = self.scrape_stat_page('fumbles-lost-per-game')
        time.sleep(1)

        offensive_tds = self.scrape_stat_page('offensive-touchdowns-per-game')
        time.sleep(1)

        passing_tds = self.scrape_stat_page('passing-touchdowns-per-game')
        time.sleep(1)

        rushing_tds = self.scrape_stat_page('rushing-touchdowns-per-game')
        time.sleep(1)

        qb_sacked = self.scrape_stat_page('qb-sacked-per-game')
        time.sleep(1)

        penalty_yards = self.scrape_stat_page('penalty-yards-per-game')
        time.sleep(1)

        plays_per_game = self.scrape_stat_page('plays-per-game')
        time.sleep(1)

        first_downs = self.scrape_stat_page('first-downs-per-game')
        time.sleep(1)

        time_of_poss = self.scrape_stat_page('time-of-possession')
        time.sleep(1)

        # Get W-L records from standings page
        records = self.scrape_standings()
        time.sleep(1)"""

# Replace the old section
old_section = """        takeaways = self.scrape_stat_page('takeaways-per-game')
        time.sleep(1)

        # Get W-L records from standings page
        records = self.scrape_standings()
        time.sleep(1)"""

content = content.replace(old_section, new_scraping_code)

# Now add the new fields to the team_stats dictionary
# Find the existing fields and add after them

old_fields_section = """                'sacks_per_game': sacks.get(team, 2.0),
                'takeaways_per_game': takeaways.get(team, 1.5),
                # Net rating approximation (point diff is close enough)
                'net_rating': point_diff.get(team, 0.0),
                'off_rating': ppg.get(team, 25.0),  # Simplified
                'def_rating': opp_ppg.get(team, 25.0),  # Simplified"""

new_fields_section = """                'sacks_per_game': sacks.get(team, 2.0),
                'takeaways_per_game': takeaways.get(team, 1.5),
                # Net rating approximation (point diff is close enough)
                'net_rating': point_diff.get(team, 0.0),
                'off_rating': ppg.get(team, 25.0),  # Simplified
                'def_rating': opp_ppg.get(team, 25.0),  # Simplified
                # NEW: Additional advanced stats (matching NFL)
                'yards_per_play': yards_per_play.get(team),
                'opponent_yards_per_play': opp_yards_per_play.get(team),
                'completion_pct': completion_pct.get(team),
                'opponent_completion_pct': opp_completion_pct.get(team),
                'fourth_down_conversion_pct': fourth_down_pct.get(team),
                'interceptions_per_game': interceptions.get(team),
                'fumbles_lost_per_game': fumbles_lost.get(team),
                'offensive_touchdowns_per_game': offensive_tds.get(team),
                'passing_touchdowns_per_game': passing_tds.get(team),
                'rushing_touchdowns_per_game': rushing_tds.get(team),
                'qb_sacked_per_game': qb_sacked.get(team),
                'penalty_yards_per_game': penalty_yards.get(team),
                'plays_per_game': plays_per_game.get(team),
                'first_downs_per_game': first_downs.get(team),
                'time_of_possession': time_of_poss.get(team)"""

content = content.replace(old_fields_section, new_fields_section)

# Write the updated file
with open('scrapers/teamrankings_ncaaf_scraper.py', 'w') as f:
    f.write(content)

print("✓ Added 15 new stat scraping calls")
print("✓ Added 15 new fields to team_stats dictionary")
print("Done!")
