#!/usr/bin/env python3
"""
Expand team name mappings to achieve 95%+ coverage
Adds 76+ new mappings for previously unmapped teams
"""

import json
import os

def expand_mappings():
    """Add comprehensive new team mappings"""

    # Load existing mappings
    mapping_file = "backend/data/team_name_mapping_complete.json"
    with open(mapping_file, 'r') as f:
        existing_mappings = json.load(f)

    print("="*70)
    print("EXPANDING TEAM NAME MAPPINGS")
    print("="*70)
    print(f"\nExisting mappings: {len(existing_mappings)}")

    # New mappings for 106 unmapped teams
    new_mappings = {
        # Core unmapped teams
        'Campbell Fighting Camels': 'Campbell',
        'Canisius Golden Griffins': 'Canisius',
        'Charleston Cougars': 'College of Charleston',
        'Charleston Southern Buccaneers': 'Charleston Southern',
        'Charlotte 49ers': 'Charlotte',
        'Cleveland St Vikings': 'Cleveland State',
        'Colorado Buffaloes': 'Colorado',
        'Columbia Lions': 'Columbia',
        'Cornell Big Red': 'Cornell',
        'Creighton Bluejays': 'Creighton',
        'Dartmouth Big Green': 'Dartmouth',
        'Delaware Blue Hens': 'Delaware',
        'East Tennessee St Buccaneers': 'East Tennessee State',
        'Eastern Kentucky Colonels': 'Eastern Kentucky',
        'Evansville Purple Aces': 'Evansville',
        'Florida A&M Rattlers': 'Florida A&M',
        "Florida Int'l Golden Panthers": 'Florida International',
        'Fort Wayne Mastodons': 'Purdue Fort Wayne',
        'Furman Paladins': 'Furman',
        'GW Revolutionaries': 'George Washington',
        'George Mason Patriots': 'George Mason',
        'Georgetown Hoyas': 'Georgetown',
        'Georgia Tech Yellow Jackets': 'Georgia Tech',
        'Grand Canyon Antelopes': 'Grand Canyon',
        "Hawai'i Rainbow Warriors": 'Hawaiʻi',
        'Hofstra Pride': 'Hofstra',
        'Houston Baptist Huskies': 'Houston Christian',  # School renamed
        'IUPUI Jaguars': 'IUPUI',
        'Idaho State Bengals': 'Idaho State',
        'Illinois Fighting Illini': 'Illinois',
        'Indiana St Sycamores': 'Indiana State',
        'Iona Gaels': 'Iona',
        'Jacksonville Dolphins': 'Jacksonville',
        'Kent State Golden Flashes': 'Kent State',
        'LIU Sharks': 'LIU',
        'Lafayette Leopards': 'Lafayette',
        'Le Moyne Dolphins': 'Le Moyne',
        'Lindenwood Lions': 'Lindenwood',
        'Lipscomb Bisons': 'Lipscomb',
        'Long Beach St 49ers': 'Long Beach State',
        "Louisiana Ragin' Cajuns": 'Louisiana',
        'Loyola (MD) Greyhounds': 'Loyola (MD)',
        'Maine Black Bears': 'Maine',
        'Manhattan Jaspers': 'Manhattan',
        'Marist Red Foxes': 'Marist',
        'Marquette Golden Eagles': 'Marquette',
        'Massachusetts Minutemen': 'UMass',
        'McNeese Cowboys': 'McNeese',
        'Miami (OH) RedHawks': 'Miami (OH)',
        'Miami Hurricanes': 'Miami (FL)',
        'Miss Valley St Delta Devils': 'Mississippi Valley State',
        'Monmouth Hawks': 'Monmouth',
        'Murray St Racers': 'Murray State',
        'NJIT Highlanders': 'NJIT',
        'Nebraska Cornhuskers': 'Nebraska',
        'Nevada Wolf Pack': 'Nevada',
        'New Orleans Privateers': 'New Orleans',
        'Niagara Purple Eagles': 'Niagara',
        'Nicholls St Colonels': 'Nicholls State',
        'North Dakota Fighting Hawks': 'North Dakota',
        'North Florida Ospreys': 'North Florida',
        'Notre Dame Fighting Irish': 'Notre Dame',
        'Oakland Golden Grizzlies': 'Oakland',
        'Omaha Mavericks': 'Omaha',
        'Oral Roberts Golden Eagles': 'Oral Roberts',
        'Pennsylvania Quakers': 'Penn',
        'Pepperdine Waves': 'Pepperdine',
        'Pittsburgh Panthers': 'Pittsburgh',
        'Portland Pilots': 'Portland',
        'Presbyterian Blue Hose': 'Presbyterian',
        'Queens University Royals': 'Queens (NC)',
        'Radford Highlanders': 'Radford',
        'Rider Broncs': 'Rider',
        'Rutgers Scarlet Knights': 'Rutgers',
        'SE Louisiana Lions': 'Southeastern Louisiana',
        'SE Missouri St Redhawks': 'Southeast Missouri State',
        "Saint Joseph's Hawks": "Saint Joseph's",
        "Saint Mary's Gaels": "Saint Mary's (CA)",
        'Sam Houston St Bearkats': 'Sam Houston State',
        'San Diego Toreros': 'San Diego',
        'San José St Spartans': 'San Jose State',
        'Siena Saints': 'Siena',
        'South Dakota Coyotes': 'South Dakota',
        'Southern Indiana Screaming Eagles': 'Southern Indiana',
        'Southern Utah Thunderbirds': 'Southern Utah',
        'St. Thomas (MN) Tommies': 'St. Thomas (MN)',
        'Stanford Cardinal': 'Stanford',
        'Stetson Hatters': 'Stetson',
        'Stonehill Skyhawks': 'Stonehill',
        'Syracuse Orange': 'Syracuse',
        'TCU Horned Frogs': 'TCU',
        'Tarleton State Texans': 'Tarleton State',
        'Tenn-Martin Skyhawks': 'UT Martin',
        'Tennessee Tech Golden Eagles': 'Tennessee Tech',
        'Texas A&M-CC Islanders': 'Texas A&M-Corpus Chris',
        'Texas A&M-Commerce Lions': 'Texas A&M-Commerce',
        'Tulane Green Wave': 'Tulane',
        'Tulsa Golden Hurricane': 'Tulsa',
        'UAB Blazers': 'UAB',
        'UL Monroe Warhawks': 'ULM',
        'UT-Arlington Mavericks': 'UT Arlington',
        'Utah Tech Trailblazers': 'Utah Tech',
        'VMI Keydets': 'VMI',
        'Valparaiso Beacons': 'Valparaiso',
        'Vanderbilt Commodores': 'Vanderbilt',
        'Wagner Seahawks': 'Wagner',
    }

    # Merge with existing
    updated_mappings = {**existing_mappings, **new_mappings}

    print(f"Adding: {len(new_mappings)} new mappings")
    print(f"Total mappings: {len(updated_mappings)}")

    # Save updated mappings
    with open(mapping_file, 'w') as f:
        json.dump(updated_mappings, f, indent=2)

    print(f"\nSaved updated mappings to {mapping_file}")
    print("="*70)

    return len(new_mappings), len(updated_mappings)


if __name__ == "__main__":
    new_count, total_count = expand_mappings()
    print(f"\nSUCCESS: Added {new_count} mappings")
    print(f"Total coverage: {total_count} teams")
