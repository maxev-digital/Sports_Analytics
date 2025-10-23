/**
 * Comprehensive Bookmaker Data
 * Includes URLs, logos, and display names for all bookmakers
 */

const BOOKMAKERS = {
  // US Bookmakers
  'draftkings': {
    name: 'DraftKings',
    url: 'https://sportsbook.draftkings.com/leagues/basketball/nba',
    logo: 'https://www.google.com/s2/favicons?domain=draftkings.com&sz=64',
    region: 'US'
  },
  'fanduel': {
    name: 'FanDuel',
    url: 'https://sportsbook.fanduel.com/navigation/nba',
    logo: 'https://www.google.com/s2/favicons?domain=fanduel.com&sz=64',
    region: 'US'
  },
  'betmgm': {
    name: 'BetMGM',
    url: 'https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004',
    logo: 'https://www.google.com/s2/favicons?domain=betmgm.com&sz=64',
    region: 'US'
  },
  'betrivers': {
    name: 'BetRivers',
    url: 'https://www.betrivers.com/?page=sportsbook#basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betrivers.com&sz=64',
    region: 'US'
  },
  'williamhill_us': {
    name: 'William Hill',
    url: 'https://www.williamhill.com/us/nv/bet/en/betting/t/basketball/nba',
    logo: 'https://www.google.com/s2/favicons?domain=williamhill.com&sz=64',
    region: 'US'
  },
  'fanatics': {
    name: 'Fanatics',
    url: 'https://fanatics.com/sportsbook/basketball/nba',
    logo: 'https://www.google.com/s2/favicons?domain=fanatics.com&sz=64',
    region: 'US'
  },
  'espnbet': {
    name: 'ESPN BET',
    url: 'https://espnbet.com/sport/basketball/usa/nba',
    logo: 'https://www.google.com/s2/favicons?domain=espnbet.com&sz=64',
    region: 'US'
  },
  'caesars': {
    name: 'Caesars',
    url: 'https://www.caesars.com/sportsbook-and-casino/basketball/nba',
    logo: 'https://www.google.com/s2/favicons?domain=caesars.com&sz=64',
    region: 'US'
  },
  'pointsbet': {
    name: 'PointsBet',
    url: 'https://pointsbet.com/sports/basketball/nba',
    logo: 'https://www.google.com/s2/favicons?domain=pointsbet.com&sz=64',
    region: 'US'
  },
  'ballybet': {
    name: 'Bally Bet',
    url: 'https://ballybet.com/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=ballybet.com&sz=64',
    region: 'US'
  },
  'betonlineag': {
    name: 'BetOnline',
    url: 'https://www.betonline.ag/sportsbook/basketball/nba',
    logo: 'https://www.google.com/s2/favicons?domain=betonline.ag&sz=64',
    region: 'US'
  },
  'bovada': {
    name: 'Bovada',
    url: 'https://www.bovada.lv/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=bovada.lv&sz=64',
    region: 'US'
  },
  'mybookieag': {
    name: 'MyBookie',
    url: 'https://www.mybookie.ag/sportsbook/nba/',
    logo: 'https://www.google.com/s2/favicons?domain=mybookie.ag&sz=64',
    region: 'US'
  },
  'lowvig': {
    name: 'LowVig',
    url: 'https://lowvig.ag/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=lowvig.ag&sz=64',
    region: 'US'
  },
  'betway': {
    name: 'Betway',
    url: 'https://sports.betway.com/en/sports/grp/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betway.com&sz=64',
    region: 'US'
  },
  'betanysports': {
    name: 'BetAnySports',
    url: 'https://www.betanysports.com/sportsbook/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betanysports.com&sz=64',
    region: 'US'
  },
  'betparx': {
    name: 'BetParx',
    url: 'https://www.betparx.com/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betparx.com&sz=64',
    region: 'US'
  },
  'fliff': {
    name: 'Fliff',
    url: 'https://fliff.com/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=fliff.com&sz=64',
    region: 'US'
  },
  'gtbets': {
    name: 'GTBets',
    url: 'https://www.gtbets.ag/sportsbook/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=gtbets.ag&sz=64',
    region: 'US'
  },
  'hardrockbet': {
    name: 'Hard Rock Bet',
    url: 'https://www.hardrockbet.com/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=hardrockbet.com&sz=64',
    region: 'US'
  },
  'betus': {
    name: 'BetUS',
    url: 'https://www.betus.com.pa/sportsbook/basketball/',
    logo: 'https://www.google.com/s2/favicons?domain=betus.com.pa&sz=64',
    region: 'US'
  },

  // UK Bookmakers
  'williamhill': {
    name: 'William Hill UK',
    url: 'https://sports.williamhill.com/betting/en-gb/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=williamhill.com&sz=64',
    region: 'UK'
  },
  'ladbrokes_uk': {
    name: 'Ladbrokes',
    url: 'https://sports.ladbrokes.com/en-gb/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=ladbrokes.com&sz=64',
    region: 'UK'
  },
  'coral': {
    name: 'Coral',
    url: 'https://sports.coral.co.uk/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=coral.co.uk&sz=64',
    region: 'UK'
  },
  'betfair_sb_uk': {
    name: 'Betfair Sportsbook',
    url: 'https://www.betfair.com/sport/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betfair.com&sz=64',
    region: 'UK'
  },
  'betfair_ex_uk': {
    name: 'Betfair Exchange',
    url: 'https://www.betfair.com/exchange/plus/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betfair.com&sz=64',
    region: 'UK'
  },
  'paddypower': {
    name: 'Paddy Power',
    url: 'https://www.paddypower.com/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=paddypower.com&sz=64',
    region: 'UK'
  },
  'boylesports': {
    name: 'BoyleSports',
    url: 'https://www.boylesports.com/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=boylesports.com&sz=64',
    region: 'UK'
  },
  'unibet_uk': {
    name: 'Unibet UK',
    url: 'https://www.unibet.co.uk/betting/sports/filter/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=unibet.co.uk&sz=64',
    region: 'UK'
  },
  'virginbet': {
    name: 'Virgin Bet',
    url: 'https://virginbet.com/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=virginbet.com&sz=64',
    region: 'UK'
  },
  'grosvenor': {
    name: 'Grosvenor',
    url: 'https://www.grosvenorcasinos.com/sport/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=grosvenorcasinos.com&sz=64',
    region: 'UK'
  },
  'livescorebet': {
    name: 'LiveScore Bet',
    url: 'https://www.livescorebet.com/en/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=livescorebet.com&sz=64',
    region: 'UK'
  },

  // Australian Bookmakers
  'sportsbet': {
    name: 'Sportsbet',
    url: 'https://www.sportsbet.com.au/betting/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=sportsbet.com.au&sz=64',
    region: 'AU'
  },
  'tab': {
    name: 'TAB',
    url: 'https://www.tab.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=tab.com.au&sz=64',
    region: 'AU'
  },
  'ladbrokes_au': {
    name: 'Ladbrokes AU',
    url: 'https://www.ladbrokes.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=ladbrokes.com.au&sz=64',
    region: 'AU'
  },
  'neds': {
    name: 'Neds',
    url: 'https://www.neds.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=neds.com.au&sz=64',
    region: 'AU'
  },
  'pointsbetau': {
    name: 'PointsBet AU',
    url: 'https://pointsbet.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=pointsbet.com.au&sz=64',
    region: 'AU'
  },
  'betfair_ex_au': {
    name: 'Betfair AU',
    url: 'https://www.betfair.com.au/exchange/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betfair.com.au&sz=64',
    region: 'AU'
  },
  'betr_au': {
    name: 'Betr',
    url: 'https://www.betr.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betr.com.au&sz=64',
    region: 'AU'
  },
  'playup': {
    name: 'PlayUp',
    url: 'https://www.playup.com/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=playup.com&sz=64',
    region: 'AU'
  },
  'dabble_au': {
    name: 'Dabble',
    url: 'https://www.dabble.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=dabble.com.au&sz=64',
    region: 'AU'
  },
  'boombet': {
    name: 'BoomBet',
    url: 'https://www.boombet.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=boombet.com.au&sz=64',
    region: 'AU'
  },
  'betright': {
    name: 'BetRight',
    url: 'https://www.betright.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betright.com.au&sz=64',
    region: 'AU'
  },
  'tabtouch': {
    name: 'TABtouch',
    url: 'https://www.tabtouch.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=tabtouch.com.au&sz=64',
    region: 'AU'
  },
  'rebet': {
    name: 'Rebet',
    url: 'https://www.rebet.com.au/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=rebet.com.au&sz=64',
    region: 'AU'
  },

  // European Bookmakers
  'unibet': {
    name: 'Unibet',
    url: 'https://www.unibet.com/betting/sports/filter/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=unibet.com&sz=64',
    region: 'EU'
  },
  'betsson': {
    name: 'Betsson',
    url: 'https://www.betsson.com/en/sportsbook/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betsson.com&sz=64',
    region: 'EU'
  },
  'nordicbet': {
    name: 'NordicBet',
    url: 'https://www.nordicbet.com/en/sportsbook/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=nordicbet.com&sz=64',
    region: 'EU'
  },
  'marathonbet': {
    name: 'Marathon Bet',
    url: 'https://www.marathonbet.com/en/betting/Basketball',
    logo: 'https://www.google.com/s2/favicons?domain=marathonbet.com&sz=64',
    region: 'EU'
  },
  'pinnacle': {
    name: 'Pinnacle',
    url: 'https://www.pinnacle.com/en/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=pinnacle.com&sz=64',
    region: 'EU'
  },
  'onexbet': {
    name: '1xBet',
    url: 'https://www.1xbet.com/en/line/Basketball',
    logo: 'https://www.google.com/s2/favicons?domain=1xbet.com&sz=64',
    region: 'EU'
  },
  'betfair_ex_eu': {
    name: 'Betfair EU',
    url: 'https://www.betfair.com/exchange/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betfair.com&sz=64',
    region: 'EU'
  },
  'leovegas': {
    name: 'LeoVegas',
    url: 'https://www.leovegas.com/en-row/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=leovegas.com&sz=64',
    region: 'EU'
  },
  'coolbet': {
    name: 'Coolbet',
    url: 'https://www.coolbet.com/en/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=coolbet.com&sz=64',
    region: 'EU'
  },
  'casumo': {
    name: 'Casumo',
    url: 'https://www.casumo.com/en/sports/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=casumo.com&sz=64',
    region: 'EU'
  },
  'sport888': {
    name: '888sport',
    url: 'https://www.888sport.com/#/filter/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=888sport.com&sz=64',
    region: 'EU'
  },
  'smarkets': {
    name: 'Smarkets',
    url: 'https://smarkets.com/listing/sport/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=smarkets.com&sz=64',
    region: 'EU'
  },
  'unibet_it': {
    name: 'Unibet IT',
    url: 'https://www.unibet.it/scommesse/sport/filter/basket',
    logo: 'https://www.google.com/s2/favicons?domain=unibet.it&sz=64',
    region: 'IT'
  },
  'unibet_nl': {
    name: 'Unibet NL',
    url: 'https://www.unibet.nl/wedden/sport/filter/basketbal',
    logo: 'https://www.google.com/s2/favicons?domain=unibet.nl&sz=64',
    region: 'NL'
  },
  'unibet_se': {
    name: 'Unibet SE',
    url: 'https://www.unibet.se/betting/sports/filter/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=unibet.se&sz=64',
    region: 'SE'
  },
  'betclic_fr': {
    name: 'Betclic',
    url: 'https://www.betclic.fr/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=betclic.fr&sz=64',
    region: 'FR'
  },
  'parionssport_fr': {
    name: 'ParionsSport',
    url: 'https://www.parionssport.fdj.fr/paris-basket',
    logo: 'https://www.google.com/s2/favicons?domain=parionssport.fdj.fr&sz=64',
    region: 'FR'
  },
  'winamax_fr': {
    name: 'Winamax FR',
    url: 'https://www.winamax.fr/paris-sportifs/sports/8/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=winamax.fr&sz=64',
    region: 'FR'
  },
  'winamax_de': {
    name: 'Winamax DE',
    url: 'https://www.winamax.de/wetten/sports/8/basketball',
    logo: 'https://www.google.com/s2/favicons?domain=winamax.de&sz=64',
    region: 'DE'
  },
  'tipico_de': {
    name: 'Tipico',
    url: 'https://www.tipico.de/de/sport/basketball/',
    logo: 'https://www.google.com/s2/favicons?domain=tipico.de&sz=64',
    region: 'DE'
  }
};

// Helper function to get bookmaker data
function getBookmaker(key) {
  return BOOKMAKERS[key] || {
    name: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    url: '#',
    logo: 'https://www.google.com/s2/favicons?domain=example.com&sz=64',
    region: 'Unknown'
  };
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BOOKMAKERS, getBookmaker };
}
