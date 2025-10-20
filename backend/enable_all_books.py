import requests

# All 62 bookmakers
all_bookmakers = [
    "draftkings", "fanduel", "betmgm", "caesars", "betrivers", "pointsbet", "williamhill_us",
    "espnbet", "wynnbet", "fanatics", "betonlineag", "mybookieag", "bovada", "lowvig", "betus",
    "gtbets", "intertops", "bookmaker", "pinnacle", "bet365", "williamhill", "paddypower",
    "betfair", "betway", "marathonbet", "matchbook", "smarkets", "betvictor", "livescorebet",
    "virginbet", "grosvenor", "casumo", "888sport", "unibet", "betsson", "nordicbet", "coolbet",
    "leovegas", "betclic", "bwin", "betparx", "sisportsbook", "hardrockbet", "ballybet", "fliff",
    "betuk", "skybet", "ladbrokes", "coral", "sportsbetau", "tabtouch", "pointsbetau", "neds",
    "unibet_au", "betr_au", "topsport", "unibet_se", "unibet_nl", "unibet_it", "tipico",
    "supabets", "playup"
]

response = requests.put(
    "http://localhost:8002/api/settings/bookmakers",
    params={"user_id": "default"},
    json={"enabled_bookmakers": all_bookmakers}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
