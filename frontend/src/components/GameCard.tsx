import { useState } from 'react';
import { LiveGame } from '../types';
import { detectSport, getSportEmoji, getSportGradientClasses, getSportBorderClass } from '../utils/sportDetection';
import { BOOKMAKERS } from '../data/bookmakers';
import { openSportsbook } from '../utils/deepLinking';
import { getGameSpecificUrl } from '../utils/gameUrls';
import { trackBetClick } from '../utils/betTracking';
import { useAuth } from '../contexts/AuthContext';

interface GameCardProps {
  game: LiveGame;
}

// Sportsbook logo URLs and fallback badges
const getBookmakerInfo = (bookmaker: string) => {
  // Normalize bookmaker name to match BOOKMAKERS keys
  // API returns: "MyBookie.ag", "Nordic Bet", "DraftKings"
  // Database keys: "mybookieag", "nordicbet", "draftkings"
  const normalizedKey = bookmaker
    .toLowerCase()
    .replace(/\s+/g, '')      // Remove all spaces: "Nordic Bet" -> "nordicbet"
    .replace(/\./g, '')       // Remove periods: "MyBookie.ag" -> "mybookieag"
    .replace(/_/g, '');       // Remove underscores if any

  // Try to find in BOOKMAKERS database
  const bookmakerData = BOOKMAKERS[normalizedKey];

  if (bookmakerData) {
    return {
      logo: bookmakerData.logo,
      short: bookmaker.substring(0, 3).toUpperCase(),
      bg: 'bg-slate-800',
      text: 'text-slate-200'
    };
  }

  // Fallback to old hardcoded data
  return getBookmakerInfoFallback(bookmaker);
};

const getBookmakerInfoFallback = (bookmaker: string) => {
  const bookmakers: Record<string, { logo: string; short: string; bg: string; text: string }> = {
    'DraftKings': {
      logo: 'https://sportsbook-brands.draftkings.com/images/dk-sportsbook-logo.svg',
      short: 'DK',
      bg: 'bg-green-900',
      text: 'text-green-200'
    },
    'FanDuel': {
      logo: 'https://www.fanduel.com/favicon.svg',
      short: 'FD',
      bg: 'bg-blue-900',
      text: 'text-blue-200'
    },
    'BetMGM': {
      logo: 'https://sports.betmgm.com/assets/img/logos/betmgm-logo.svg',
      short: 'MGM',
      bg: 'bg-yellow-900',
      text: 'text-yellow-200'
    },
    'Caesars': {
      logo: 'https://www.caesars.com/sportsbook-and-casino/assets/images/logo.svg',
      short: 'CZR',
      bg: 'bg-purple-900',
      text: 'text-purple-200'
    },
    'BetRivers': {
      logo: 'https://www.betrivers.com/etc.clientlibs/betrivers/clientlibs/clientlib-base/resources/images/betrivers-logo.svg',
      short: 'BR',
      bg: 'bg-cyan-900',
      text: 'text-cyan-200'
    },
    'Bovada': {
      logo: 'https://www.bovada.lv/favicon.ico',
      short: 'BOV',
      bg: 'bg-red-900',
      text: 'text-red-200'
    },
    'BetOnline.ag': {
      logo: 'https://www.betonline.ag/images/betonline-logo.svg',
      short: 'BOL',
      bg: 'bg-orange-900',
      text: 'text-orange-200'
    },
    'MyBookie.ag': {
      logo: 'https://www.mybookie.ag/favicon.ico',
      short: 'MB',
      bg: 'bg-pink-900',
      text: 'text-pink-200'
    },
    'BetUS': {
      logo: 'https://www.betus.com.pa/favicon.ico',
      short: 'BUS',
      bg: 'bg-indigo-900',
      text: 'text-indigo-200'
    },
    'LowVig.ag': {
      logo: 'https://lowvig.ag/favicon.ico',
      short: 'LV',
      bg: 'bg-teal-900',
      text: 'text-teal-200'
    },
    'Fanatics': {
      logo: 'https://www.fanaticssportsbook.com/favicon.ico',
      short: 'FAN',
      bg: 'bg-slate-800',
      text: 'text-slate-200'
    },
  };
  return bookmakers[bookmaker] || {
    logo: '',
    short: bookmaker.substring(0, 3).toUpperCase(),
    bg: 'bg-slate-800',
    text: 'text-slate-300'
  };
};

export function GameCard({ game }: GameCardProps) {
  const { state, odds, projection, home_team_stats, away_team_stats, home_nfl_live_stats, away_nfl_live_stats, home_nfl_stats, away_nfl_stats, home_nhl_momentum, away_nhl_momentum, home_nhl_stats, away_nhl_stats, home_nba_momentum, away_nba_momentum, home_nfl_momentum, away_nfl_momentum, home_ncaaf_momentum, away_ncaaf_momentum } = game;

  // Get username for bet tracking
  const { username } = useAuth();

  // Stats view toggle: 'stats' (raw stats), 'rankings' (ranks only), 'combined' (stats + ranks)
  const [statsView, setStatsView] = useState<'stats' | 'rankings' | 'combined'>('stats');

  // Market type toggle: 'spread', 'moneyline', 'totals'
  const [selectedMarket, setSelectedMarket] = useState<'spread' | 'moneyline' | 'totals'>('totals');

  // Handle bet tracking when bookmaker is clicked
  const handleBookmakerClick = async (bookmakerName: string, odd: any, bookmakerUrl: string) => {
    // Only track bet if user is logged in
    if (!username) {
      openSportsbook(bookmakerUrl, bookmakerName);
      return;
    }

    // Determine bet details based on selected market and projection recommendation
    let betType: 'spread' | 'total' | 'moneyline' | 'prop' = 'total';
    let betSide = '';
    let betOdds = 0;

    if (selectedMarket === 'totals') {
      betType = 'total';
      // Use projection recommendation if available, otherwise default to OVER
      if (projection.recommendation === 'OVER') {
        betSide = 'OVER';
        betOdds = odd.over_price;
      } else if (projection.recommendation === 'UNDER') {
        betSide = 'UNDER';
        betOdds = odd.under_price;
      } else {
        // Default to OVER if no recommendation
        betSide = 'OVER';
        betOdds = odd.over_price;
      }
    } else if (selectedMarket === 'spread') {
      betType = 'spread';
      // Default to home team spread, but use projection if available
      betSide = `${state.home_team.name} ${odd.home_spread > 0 ? '+' : ''}${odd.home_spread}`;
      betOdds = odd.home_spread_price;
    } else if (selectedMarket === 'moneyline') {
      betType = 'moneyline';
      // Default to home team ML
      betSide = state.home_team.name;
      betOdds = odd.home_ml;
    }

    // Track the bet click
    try {
      await trackBetClick({
        userId: username,
        gameId: state.id,
        sport: state.sport_key,
        homeTeam: state.home_team.name,
        awayTeam: state.away_team.name,
        commenceTime: state.commence_time,
        betType,
        betSide,
        odds: betOdds,
        bookmaker: bookmakerName,
        confidence: projection.confidence as 'HIGH' | 'MEDIUM' | 'LOW' | undefined,
        edgePercent: projection.edge ? Math.abs(projection.edge) : undefined,
      });

      console.log(`✅ Bet tracked: ${betSide} at ${betOdds} via ${bookmakerName}`);
    } catch (error) {
      console.error('Failed to track bet:', error);
    }

    // Open sportsbook
    openSportsbook(bookmakerUrl, bookmakerName);
  };

  // Helper function to get rank color (green for top 10, yellow for 11-20, white for 21+)
  const getRankColor = (rank: number) => {
    if (rank <= 10) return 'text-green-400';
    if (rank <= 20) return 'text-yellow-400';
    return '${textSecondary}';
  };

  // Determine sport type from sport_key
  const sportBadge = state.sport_key?.includes('icehockey') ? 'NHL' :
                     state.sport_key?.includes('americanfootball_ncaaf') ? 'NCAAF' :
                     state.sport_key?.includes('americanfootball_nfl') ? 'NFL' :
                     state.sport_key?.includes('baseball_mlb') ? 'MLB' :
                     state.sport_key?.includes('basketball_nba') ? 'NBA' : 'NBA';

  // Get team logo URLs using a logo service
  const getTeamLogo = (teamName: string, sport: string) => {
    // Clean team name for logo lookup - normalize to lowercase with spaces
    const cleanName = teamName.toLowerCase();

    if (sport === 'NHL') {
      // Use ESPN's NHL team logos
      const nhlTeams: Record<string, string> = {
        'anaheim ducks': 'ana', 'arizona coyotes': 'ari', 'boston bruins': 'bos',
        'buffalo sabres': 'buf', 'calgary flames': 'cgy', 'carolina hurricanes': 'car',
        'chicago blackhawks': 'chi', 'colorado avalanche': 'col', 'columbus blue jackets': 'cbj',
        'dallas stars': 'dal', 'detroit red wings': 'det', 'edmonton oilers': 'edm',
        'florida panthers': 'fla', 'los angeles kings': 'la', 'minnesota wild': 'min',
        'montréal canadiens': 'mtl', 'montreal canadiens': 'mtl', 'nashville predators': 'nsh',
        'new jersey devils': 'njd', 'new york islanders': 'nyi', 'new york rangers': 'nyr',
        'ottawa senators': 'ott', 'philadelphia flyers': 'phi', 'pittsburgh penguins': 'pit',
        'san jose sharks': 'sj', 'seattle kraken': 'sea', 'st louis blues': 'stl',
        'st. louis blues': 'stl', 'tampa bay lightning': 'tb', 'toronto maple leafs': 'tor',
        'vancouver canucks': 'van', 'vegas golden knights': 'vgk', 'washington capitals': 'wsh',
        'winnipeg jets': 'wpg', 'utah mammoth': 'utah', 'utah hockey club': 'utah'
      };
      const abbr = nhlTeams[cleanName];
      return abbr ? `https://a.espncdn.com/i/teamlogos/nhl/500/${abbr}.png` : '';
    } else if (sport === 'NCAAF') {
      // Use ESPN's NCAAF team logos
      const ncaafTeams: Record<string, string> = {
        'alabama crimson tide': 'ala', 'arizona wildcats': 'ariz', 'arizona state sun devils': 'asu',
        'arkansas razorbacks': 'ark', 'auburn tigers': 'aub', 'baylor bears': 'bay',
        'boise state broncos': 'bsu', 'boston college eagles': 'bc', 'bowling green falcons': 'bgsu',
        'buffalo bulls': 'buf', 'california golden bears': 'cal', 'central michigan chippewas': 'cmu',
        'cincinnati bearcats': 'cin', 'clemson tigers': 'clem', 'colorado buffaloes': 'col',
        'duke blue devils': 'duke', 'east carolina pirates': 'ecu', 'florida gators': 'fla',
        'florida state seminoles': 'fsu', 'fresno state bulldogs': 'fres', 'georgia bulldogs': 'uga',
        'georgia tech yellow jackets': 'gt', 'houston cougars': 'hou', 'illinois fighting illini': 'ill',
        'indiana hoosiers': 'ind', 'iowa hawkeyes': 'iowa', 'iowa state cyclones': 'isu',
        'kansas jayhawks': 'kan', 'kansas state wildcats': 'ksu', 'kentucky wildcats': 'uk',
        'louisiana ragin cajuns': 'ul', 'louisville cardinals': 'lou', 'lsu tigers': 'lsu',
        'marshall thundering herd': 'mar', 'maryland terrapins': 'md', 'memphis tigers': 'mem',
        'miami hurricanes': 'mia', 'michigan wolverines': 'mich', 'michigan state spartans': 'msu',
        'minnesota golden gophers': 'minn', 'mississippi state bulldogs': 'miss', 'missouri tigers': 'miz',
        'nc state wolfpack': 'ncst', 'nebraska cornhuskers': 'neb', 'nevada wolf pack': 'nev',
        'north carolina tar heels': 'unc', 'northwestern wildcats': 'nw', 'notre dame fighting irish': 'nd',
        'ohio state buckeyes': 'osu', 'oklahoma sooners': 'okla', 'oklahoma state cowboys': 'okst',
        'ole miss rebels': 'miss', 'oregon ducks': 'ore', 'oregon state beavers': 'orst',
        'penn state nittany lions': 'psu', 'pittsburgh panthers': 'pitt', 'purdue boilermakers': 'pur',
        'rutgers scarlet knights': 'rutg', 'san diego state aztecs': 'sdsu', 'south carolina gamecocks': 'sc',
        'smu mustangs': 'smu', 'stanford cardinal': 'stan', 'syracuse orange': 'syr',
        'tcu horned frogs': 'tcu', 'temple owls': 'tem', 'tennessee volunteers': 'tenn',
        'texas longhorns': 'tex', 'texas a&m aggies': 'tamu', 'texas tech red raiders': 'tt',
        'toledo rockets': 'tol', 'troy trojans': 'troy', 'tulane green wave': 'tul',
        'ucla bruins': 'ucla', 'usc trojans': 'usc', 'utah utes': 'utah',
        'vanderbilt commodores': 'van', 'virginia cavaliers': 'uva', 'virginia tech hokies': 'vt',
        'wake forest demon deacons': 'wake', 'washington huskies': 'wash', 'washington state cougars': 'wsu',
        'west virginia mountaineers': 'wvu', 'wisconsin badgers': 'wisc', 'wyoming cowboys': 'wyo',
        'james madison dukes': 'jmu', 'liberty flames': 'lib', 'georgia state panthers': 'gast',
        // Additional FBS teams
        'umass minutemen': 'umass', 'kent state golden flashes': 'kent', 'air force falcons': 'afa',
        'unlv rebels': 'unlv', 'old dominion monarchs': 'odu', 'ball state cardinals': 'ball',
        'western michigan broncos': 'wmu', 'appalachian state mountaineers': 'app', 'navy midshipmen': 'navy',
        'uab blazers': 'uab', 'florida atlantic owls': 'fau', 'ul monroe warhawks': 'ulm',
        'coastal carolina chanticleers': 'ccu', 'san jose state spartans': 'sjsu', 'rice owls': 'rice',
        'utsa roadrunners': 'utsa', 'byu cougars': 'byu', 'texas state bobcats': 'txst',
        'new mexico lobos': 'unm', 'utah state aggies': 'usu', 'hawaii rainbow warriors': 'haw',
        'new mexico state aggies': 'nmsu', 'arkansas state red wolves': 'arst', 'south alabama jaguars': 'usa',
        'florida international panthers': 'fiu', 'western kentucky hilltoppers': 'wku',
        'jacksonville state gamecocks': 'jvst', 'utep miners': 'utep', 'sam houston state bearkats': 'shsu',
        'tulsa golden hurricane': 'tulsa', 'delaware blue hens': 'del'
      };
      const abbr = ncaafTeams[cleanName];
      return abbr ? `https://a.espncdn.com/i/teamlogos/ncaa/500/${abbr}.png` : '';
    } else if (sport === 'NFL') {
      // Use ESPN's NFL team logos
      const nflTeams: Record<string, string> = {
        'arizona cardinals': 'ari', 'atlanta falcons': 'atl', 'baltimore ravens': 'bal',
        'buffalo bills': 'buf', 'carolina panthers': 'car', 'chicago bears': 'chi',
        'cincinnati bengals': 'cin', 'cleveland browns': 'cle', 'dallas cowboys': 'dal',
        'denver broncos': 'den', 'detroit lions': 'det', 'green bay packers': 'gb',
        'houston texans': 'hou', 'indianapolis colts': 'ind', 'jacksonville jaguars': 'jax',
        'kansas city chiefs': 'kc', 'las vegas raiders': 'lv', 'los angeles chargers': 'lac',
        'los angeles rams': 'lar', 'miami dolphins': 'mia', 'minnesota vikings': 'min',
        'new england patriots': 'ne', 'new orleans saints': 'no', 'new york giants': 'nyg',
        'new york jets': 'nyj', 'philadelphia eagles': 'phi', 'pittsburgh steelers': 'pit',
        'san francisco 49ers': 'sf', 'seattle seahawks': 'sea', 'tampa bay buccaneers': 'tb',
        'tennessee titans': 'ten', 'washington commanders': 'wsh'
      };
      const abbr = nflTeams[cleanName];
      return abbr ? `https://a.espncdn.com/i/teamlogos/nfl/500/${abbr}.png` : '';
    } else if (sport === 'MLB') {
      // Use ESPN's MLB team logos
      const mlbTeams: Record<string, string> = {
        'arizona diamondbacks': 'ari', 'atlanta braves': 'atl', 'baltimore orioles': 'bal',
        'boston red sox': 'bos', 'chicago cubs': 'chc', 'chicago white sox': 'chw',
        'cincinnati reds': 'cin', 'cleveland guardians': 'cle', 'colorado rockies': 'col',
        'detroit tigers': 'det', 'houston astros': 'hou', 'kansas city royals': 'kc',
        'los angeles angels': 'laa', 'los angeles dodgers': 'lad', 'miami marlins': 'mia',
        'milwaukee brewers': 'mil', 'minnesota twins': 'min', 'new york mets': 'nym',
        'new york yankees': 'nyy', 'oakland athletics': 'oak', 'philadelphia phillies': 'phi',
        'pittsburgh pirates': 'pit', 'san diego padres': 'sd', 'san francisco giants': 'sf',
        'seattle mariners': 'sea', 'st louis cardinals': 'stl', 'st. louis cardinals': 'stl',
        'tampa bay rays': 'tb', 'texas rangers': 'tex', 'toronto blue jays': 'tor',
        'washington nationals': 'wsh'
      };
      const abbr = mlbTeams[cleanName];
      return abbr ? `https://a.espncdn.com/i/teamlogos/mlb/500/${abbr}.png` : '';
    } else {
      // Use ESPN's NBA team logos
      const nbaTeams: Record<string, string> = {
        'atlanta hawks': 'atl', 'boston celtics': 'bos', 'brooklyn nets': 'bkn',
        'charlotte hornets': 'cha', 'chicago bulls': 'chi', 'cleveland cavaliers': 'cle',
        'dallas mavericks': 'dal', 'denver nuggets': 'den', 'detroit pistons': 'det',
        'golden state warriors': 'gs', 'houston rockets': 'hou', 'indiana pacers': 'ind',
        'los angeles clippers': 'lac', 'los angeles lakers': 'lal', 'memphis grizzlies': 'mem',
        'miami heat': 'mia', 'milwaukee bucks': 'mil', 'minnesota timberwolves': 'min',
        'new orleans pelicans': 'no', 'new york knicks': 'ny', 'oklahoma city thunder': 'okc',
        'orlando magic': 'orl', 'philadelphia 76ers': 'phi', 'phoenix suns': 'phx',
        'portland trail blazers': 'por', 'sacramento kings': 'sac', 'san antonio spurs': 'sa',
        'toronto raptors': 'tor', 'utah jazz': 'utah', 'washington wizards': 'wsh'
      };
      const abbr = nbaTeams[cleanName];
      return abbr ? `https://a.espncdn.com/i/teamlogos/nba/500/${abbr}.png` : '';
    }
  };

  const awayLogo = getTeamLogo(state.away_team.name, sportBadge);
  const homeLogo = getTeamLogo(state.home_team.name, sportBadge);

  // Debug: Log teams without logos
  if (!awayLogo) {
    console.log(`Missing logo for ${sportBadge} team: ${state.away_team.name}`);
  }
  if (!homeLogo) {
    console.log(`Missing logo for ${sportBadge} team: ${state.home_team.name}`);
  }

  // Get team colors for NFL teams
  const getTeamColors = (teamName: string): { primary: string, secondary: string } => {
    const cleanName = teamName.toLowerCase();
    const nflColors: Record<string, { primary: string, secondary: string }> = {
      'arizona cardinals': { primary: '#97233F', secondary: '#000000' },
      'atlanta falcons': { primary: '#A71930', secondary: '#000000' },
      'baltimore ravens': { primary: '#241773', secondary: '#000000' },
      'buffalo bills': { primary: '#00338D', secondary: '#C60C30' },
      'carolina panthers': { primary: '#0085CA', secondary: '#101820' },
      'chicago bears': { primary: '#C83803', secondary: '#0B162A' },
      'cincinnati bengals': { primary: '#FB4F14', secondary: '#000000' },
      'cleveland browns': { primary: '#311D00', secondary: '#FF3C00' },
      'dallas cowboys': { primary: '#003594', secondary: '#041E42' },
      'denver broncos': { primary: '#FB4F14', secondary: '#002244' },
      'detroit lions': { primary: '#0076B6', secondary: '#B0B7BC' },
      'green bay packers': { primary: '#203731', secondary: '#FFB612' },
      'houston texans': { primary: '#03202F', secondary: '#A71930' },
      'indianapolis colts': { primary: '#002C5F', secondary: '#A2AAAD' },
      'jacksonville jaguars': { primary: '#006778', secondary: '#9F792C' },
      'kansas city chiefs': { primary: '#E31837', secondary: '#FFB81C' },
      'las vegas raiders': { primary: '#000000', secondary: '#A5ACAF' },
      'los angeles chargers': { primary: '#0080C6', secondary: '#FFC20E' },
      'los angeles rams': { primary: '#003594', secondary: '#FFA300' },
      'miami dolphins': { primary: '#008E97', secondary: '#FC4C02' },
      'minnesota vikings': { primary: '#4F2683', secondary: '#FFC62F' },
      'new england patriots': { primary: '#002244', secondary: '#C60C30' },
      'new orleans saints': { primary: '#D3BC8D', secondary: '#101820' },
      'new york giants': { primary: '#0B2265', secondary: '#A71930' },
      'new york jets': { primary: '#125740', secondary: '#000000' },
      'philadelphia eagles': { primary: '#004C54', secondary: '#A5ACAF' },
      'pittsburgh steelers': { primary: '#FFB612', secondary: '#101820' },
      'san francisco 49ers': { primary: '#AA0000', secondary: '#B3995D' },
      'seattle seahawks': { primary: '#002244', secondary: '#69BE28' },
      'tampa bay buccaneers': { primary: '#D50A0A', secondary: '#FF7900' },
      'tennessee titans': { primary: '#0C2340', secondary: '#4B92DB' },
      'washington commanders': { primary: '#5A1414', secondary: '#FFB612' },
    };
    return nflColors[cleanName] || { primary: '#3B82F6', secondary: '#EF4444' }; // Default blue/red
  };

  const awayTeamColors = getTeamColors(state.away_team.name);
  const homeTeamColors = getTeamColors(state.home_team.name);

  // Format time
  const gameTime = new Date(state.commence_time).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'America/Chicago'
  });

  const gameDate = new Date(state.commence_time).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'America/Chicago'
  });

  // Get average total from odds
  const avgTotal = odds.length > 0
    ? (odds.reduce((sum, o) => sum + o.total, 0) / odds.length).toFixed(1)
    : '---';

  // Determine card styling based on edge
  const hasEdge = projection.edge !== null && Math.abs(projection.edge) >= 5;
  const edgeClass = hasEdge
    ? projection.recommendation === 'OVER'
      ? 'border-green-500'
      : 'border-red-500'
    : 'border-slate-700';

  // All sports use the same background color
  const bgColor = 'bg-slate-800';

  // Sport detection and NHL-specific styling
  const sport = detectSport(game);
  const sportGradient = getSportGradientClasses(sport);
  const sportBorder = getSportBorderClass(sport);
  const sportEmoji = getSportEmoji(sport);

  // Sport-specific styling
  const isNHL = sport === 'NHL';
  const isNBA = sport === 'NBA';
  const isTennis = sport === 'TENNIS';

  // Card background: NHL=ice with blue tint, Tennis=deep yellow, NBA=blue gradient, others=gradient
  const cardBackground = isNHL ? 'bg-gradient-to-br from-blue-200 via-cyan-100 to-blue-200'
    : isTennis ? 'bg-gradient-to-br from-yellow-600 to-yellow-700'
    : isNBA ? 'bg-gradient-to-br from-blue-900 to-slate-800'
    : sportGradient;
  const cardBorder = isNHL ? 'border-red-600 border-4'
    : isTennis ? 'border-2 border-yellow-400'
    : isNBA ? 'border-2 border-blue-500'
    : `border-2 ${sportBorder}`;
  const cardRounding = isNHL ? 'rounded-3xl' : isNBA ? 'rounded-lg' : 'rounded-lg';

  // Text colors
  const textPrimary = (isNHL || isTennis) ? 'text-black' : 'text-white';
  const textSecondary = (isNHL || isTennis) ? 'text-black font-bold' : 'text-slate-300';
  const textTertiary = (isNHL || isTennis) ? 'text-black font-bold' : 'text-slate-400';
  const textLabel = (isNHL || isTennis) ? 'text-black font-semibold' : 'text-slate-400';
  const textValue = (isNHL || isTennis) ? 'text-black font-bold' : 'text-slate-200';
  const textHeader = (isNHL || isTennis) ? 'text-black font-bold' : 'text-slate-100';
  const textMuted = (isNHL || isTennis) ? 'text-gray-700' : 'text-slate-500';
  const dividerClass = (isNHL || isTennis) ? '' : 'border-t border-slate-700';

  return (
    <div className={`${cardBackground} ${cardRounding} p-4 ${cardBorder} hover:shadow-lg transition-shadow relative overflow-hidden`}>
      {/* Hockey Rink Lines (NHL only) - Horizontal lines like looking down at ice */}
      {isNHL && (
        <div className="absolute inset-0 pointer-events-none opacity-15">
          {/* Goal lines (red) - 11 feet from boards in 200ft rink = ~5.5% */}
          <div className="absolute left-0 right-0 h-3 bg-red-600" style={{ top: '10%' }}></div>
          <div className="absolute left-0 right-0 h-3 bg-red-600" style={{ top: '90%' }}></div>

          {/* Blue lines - 75ft from boards in 200ft rink = 37.5% */}
          <div className="absolute left-0 right-0 h-2 bg-blue-600" style={{ top: '37.5%' }}></div>
          <div className="absolute left-0 right-0 h-2 bg-blue-600" style={{ top: '62.5%' }}></div>

          {/* Center red line - middle of rink */}
          <div className="absolute left-0 right-0 h-3 bg-red-600" style={{ top: '50%' }}></div>

          {/* Center ice circle (blue) */}
          <div className="absolute left-1/2 w-40 h-40 border-[5px] border-blue-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ top: '50%' }}></div>
          <div className="absolute left-1/2 w-4 h-4 bg-blue-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ top: '50%' }}></div>

          {/* Four face-off circles in zones (two in each end zone) */}
          {/* Top zone - left and right circles */}
          <div className="absolute w-28 h-28 border-[4px] border-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '30%', top: '23%' }}></div>
          <div className="absolute w-3 h-3 bg-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '30%', top: '23%' }}></div>

          <div className="absolute w-28 h-28 border-[4px] border-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '70%', top: '23%' }}></div>
          <div className="absolute w-3 h-3 bg-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '70%', top: '23%' }}></div>

          {/* Bottom zone - left and right circles */}
          <div className="absolute w-28 h-28 border-[4px] border-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '30%', top: '77%' }}></div>
          <div className="absolute w-3 h-3 bg-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '30%', top: '77%' }}></div>

          <div className="absolute w-28 h-28 border-[4px] border-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '70%', top: '77%' }}></div>
          <div className="absolute w-3 h-3 bg-red-600 rounded-full transform -translate-x-1/2 -translate-y-1/2" style={{ left: '70%', top: '77%' }}></div>

          {/* Goal creases (semi-circles at each end) */}
          {/* Top goal crease */}
          <div className="absolute w-24 h-14 border-[4px] border-blue-600 border-t-0 rounded-b-full transform -translate-x-1/2" style={{ left: '50%', top: '4%' }}></div>

          {/* Bottom goal crease */}
          <div className="absolute w-24 h-14 border-[4px] border-blue-600 border-b-0 rounded-t-full transform -translate-x-1/2" style={{ left: '50%', bottom: '4%' }}></div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-start mb-3 relative z-10">
        <div>
          <div className={`text-base ${textLabel}`}>{gameDate}</div>
          <div className={`text-lg font-semibold ${textSecondary}`}>{gameTime} CST</div>
        </div>
        <div className={`px-2 py-1 rounded text-base font-semibold ${
          state.status === 'live'
            ? 'bg-red-600 text-white'
            : (isNHL || isNBA) ? 'bg-gray-200 text-black' : 'bg-slate-700 ${textSecondary}'
        }`}>
          {state.status === 'live' ? 'LIVE' : 'UPCOMING'}
        </div>
      </div>

      {/* Teams */}
      <div className="space-y-3 mb-3">
        {/* Away Team */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <div className="flex items-center gap-2">
              {sportBadge !== 'NCAAF' && awayLogo && <img src={awayLogo} alt={state.away_team.name} className="w-8 h-8 object-contain" />}
              <span className={`font-medium ${textPrimary}`}>{state.away_team.name}</span>
            </div>
            {state.away_team.score !== null && (
              <span className={`text-3xl font-bold ${textPrimary}`}>{state.away_team.score}</span>
            )}
          </div>
          <div className={`flex gap-4 text-base ${sportBadge !== 'NCAAF' ? 'ml-10' : ''}`}>
            {state.away_team.spread !== null && state.away_team.spread !== undefined && (
              <div className={textSecondary}>
                <span className={textTertiary}>{isNHL ? "Puck Line: " : "Spread: "}</span>
                <span className="font-bold">{state.away_team.spread > 0 ? '+' : ''}{state.away_team.spread}</span>
                {state.away_team.spread_price && <span className="font-bold"> ({state.away_team.spread_price > 0 ? '+' : ''}{state.away_team.spread_price})</span>}
              </div>
            )}
            {state.away_team.money_line !== null && state.away_team.money_line !== undefined && (
              <div className={textSecondary}>
                <span className={textTertiary}>ML: </span>
                <span className="font-bold">{state.away_team.money_line > 0 ? '+' : ''}{state.away_team.money_line}</span>
              </div>
            )}
          </div>
        </div>

        {/* Home Team */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <div className="flex items-center gap-2">
              {sportBadge !== 'NCAAF' && homeLogo && <img src={homeLogo} alt={state.home_team.name} className="w-8 h-8 object-contain" />}
              <span className={`font-medium ${textPrimary}`}>{state.home_team.name}</span>
            </div>
            {state.home_team.score !== null && (
              <span className={`text-3xl font-bold ${textPrimary}`}>{state.home_team.score}</span>
            )}
          </div>
          <div className={`flex gap-4 text-base ${sportBadge !== 'NCAAF' ? 'ml-10' : ''}`}>
            {state.home_team.spread !== null && state.home_team.spread !== undefined && (
              <div className={textSecondary}>
                <span className={textTertiary}>{isNHL ? "Puck Line: " : "Spread: "}</span>
                <span className="font-bold">{state.home_team.spread > 0 ? '+' : ''}{state.home_team.spread}</span>
                {state.home_team.spread_price && <span className="font-bold"> ({state.home_team.spread_price > 0 ? '+' : ''}${state.home_team.spread_price})</span>}
              </div>
            )}
            {state.home_team.money_line !== null && state.home_team.money_line !== undefined && (
              <div className={textSecondary}>
                <span className={textTertiary}>ML: </span>
                <span className="font-bold">{state.home_team.money_line > 0 ? '+' : ''}{state.home_team.money_line}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Game Status - Period/Quarter/Inning Display */}
      {state.status === 'live' && state.quarter && state.time_remaining && (() => {
        // Format period/quarter based on sport
        let periodLabel = '';

        if (sportBadge === 'NHL') {
          // NHL uses periods: 1st, 2nd, 3rd, OT, 2OT, etc.
          if (state.quarter <= 3) {
            const ordinals = ['', '1st', '2nd', '3rd'];
            periodLabel = ordinals[state.quarter] || `${state.quarter}th`;
          } else {
            // Overtime periods
            const otNum = state.quarter - 3;
            periodLabel = otNum === 1 ? 'OT' : `${otNum}OT`;
          }
        } else if (sportBadge === 'MLB') {
          // MLB uses innings with Top/Bottom
          const inningNum = Math.ceil(state.quarter / 2);
          const isTop = state.quarter % 2 === 1;
          periodLabel = `${isTop ? 'Top' : 'Bot'} ${inningNum}`;
        } else {
          // NBA, NFL, NCAAF use quarters: Q1, Q2, Q3, Q4, OT, 2OT
          if (state.quarter <= 4) {
            periodLabel = `Q${state.quarter}`;
          } else {
            // Overtime periods
            const otNum = state.quarter - 4;
            periodLabel = otNum === 1 ? 'OT' : `${otNum}OT`;
          }
        }

        return (
          <div className={`text-base font-semibold ${textLabel} mb-3 flex items-center gap-2`}>
            <span className="bg-red-600 text-white px-2 py-1 rounded">{periodLabel}</span>
            <span>{state.time_remaining}</span>
          </div>
        );
      })()}

      {/* Team Momentum Bar (NBA only, live games) */}
      {sportBadge === 'NBA' && state.status === 'live' && (state.home_team.momentum !== null || state.away_team.momentum !== null) && (
        <div className="mb-3">
          <div className={`text-base ${textLabel} mb-1`}>Game Momentum</div>
          <div className="flex items-center gap-2">
            <span className={`text-base ${textLabel} w-12`}>{state.away_team.name.split(' ').pop()}</span>
            <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden relative">
              {/* Calculate momentum percentage (-100 to 100 scale) */}
              {(() => {
                const awayMomentum = state.away_team.momentum || 0;
                const homeMomentum = state.home_team.momentum || 0;
                const totalMomentum = awayMomentum + homeMomentum;
                const awayPercent = totalMomentum !== 0 ? (awayMomentum / (Math.abs(awayMomentum) + Math.abs(homeMomentum))) * 100 : 50;
                const homePercent = 100 - awayPercent;

                return (
                  <>
                    <div
                      className="absolute left-0 top-0 h-full transition-all"
                      style={{ width: `${awayPercent}%`, backgroundColor: awayTeamColors.primary }}
                    />
                    <div
                      className="absolute right-0 top-0 h-full transition-all"
                      style={{ width: `${homePercent}%`, backgroundColor: homeTeamColors.primary }}
                    />
                    {/* Center line */}
                    <div className="absolute left-1/2 top-0 h-full w-0.5 bg-white/30" style={{ transform: 'translateX(-50%)' }} />
                  </>
                );
              })()}
            </div>
            <span className={`text-base ${textLabel} w-12 text-right`}>{state.home_team.name.split(' ').pop()}</span>
          </div>
        </div>
      )}

      {/* NBA Momentum Stats (NBA only, live games) */}
      {sportBadge === 'NBA' && state.status === 'live' && (away_nba_momentum || home_nba_momentum) && (
        <div className="mb-3 border border-blue-600/30 bg-blue-900/10 rounded p-2">
          <div className="text-base text-blue-400 font-semibold mb-2">Recent Momentum (Last ~5 Min)</div>
          <div className="grid grid-cols-2 gap-3 text-base">
            {/* Away Team Momentum */}
            <div>
              <div className={`${textLabel} font-semibold mb-1`}>{state.away_team.name.split(' ').pop()}</div>
              {away_nba_momentum && (
                <>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Momentum:</span>
                    <span className={`font-semibold ${
                      away_nba_momentum.momentum_score > 60 ? 'text-green-400' :
                      away_nba_momentum.momentum_score < 40 ? 'text-red-400' : `${textSecondary}`
                    }`}>{away_nba_momentum.momentum_score.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Points:</span>
                    <span className={
                      home_nba_momentum && away_nba_momentum.points_last_5min > home_nba_momentum.points_last_5min
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nba_momentum.points_last_5min}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>FG%:</span>
                    <span className={
                      home_nba_momentum && away_nba_momentum.fg_pct_recent > home_nba_momentum.fg_pct_recent
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nba_momentum.fg_pct_recent.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Off Reb:</span>
                    <span className={
                      home_nba_momentum && away_nba_momentum.offensive_rebounds > home_nba_momentum.offensive_rebounds
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nba_momentum.offensive_rebounds}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Turnovers:</span>
                    <span className={
                      home_nba_momentum && away_nba_momentum.turnovers < home_nba_momentum.turnovers
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nba_momentum.turnovers}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Steals:</span>
                    <span className={
                      home_nba_momentum && away_nba_momentum.steals > home_nba_momentum.steals
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nba_momentum.steals}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={`${textLabel}`}>Assists:</span>
                    <span className={
                      home_nba_momentum && away_nba_momentum.assists > home_nba_momentum.assists
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nba_momentum.assists}</span>
                  </div>
                  {away_nba_momentum.possession_indicator && (
                    <div className="mt-1">
                      <span className={`text-sm px-2 py-0.5 rounded ${
                        away_nba_momentum.possession_indicator === 'ATTACKING' ? 'bg-green-900 text-green-200' :
                        away_nba_momentum.possession_indicator === 'DEFENDING' ? 'bg-red-900 text-red-200' :
                        'bg-slate-700 ${textSecondary}'
                      }`}>
                        {away_nba_momentum.possession_indicator}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Home Team Momentum */}
            <div>
              <div className={`${textLabel} font-semibold mb-1`}>{state.home_team.name.split(' ').pop()}</div>
              {home_nba_momentum && (
                <>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Momentum:</span>
                    <span className={`font-semibold ${
                      home_nba_momentum.momentum_score > 60 ? 'text-green-400' :
                      home_nba_momentum.momentum_score < 40 ? 'text-red-400' : `${textSecondary}`
                    }`}>{home_nba_momentum.momentum_score.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Points:</span>
                    <span className={
                      away_nba_momentum && home_nba_momentum.points_last_5min > away_nba_momentum.points_last_5min
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nba_momentum.points_last_5min}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>FG%:</span>
                    <span className={
                      away_nba_momentum && home_nba_momentum.fg_pct_recent > away_nba_momentum.fg_pct_recent
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nba_momentum.fg_pct_recent.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Off Reb:</span>
                    <span className={
                      away_nba_momentum && home_nba_momentum.offensive_rebounds > away_nba_momentum.offensive_rebounds
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nba_momentum.offensive_rebounds}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Turnovers:</span>
                    <span className={
                      away_nba_momentum && home_nba_momentum.turnovers < away_nba_momentum.turnovers
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nba_momentum.turnovers}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Steals:</span>
                    <span className={
                      away_nba_momentum && home_nba_momentum.steals > away_nba_momentum.steals
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nba_momentum.steals}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={`${textLabel}`}>Assists:</span>
                    <span className={
                      away_nba_momentum && home_nba_momentum.assists > away_nba_momentum.assists
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nba_momentum.assists}</span>
                  </div>
                  {home_nba_momentum.possession_indicator && (
                    <div className="mt-1">
                      <span className={`text-sm px-2 py-0.5 rounded ${
                        home_nba_momentum.possession_indicator === 'ATTACKING' ? 'bg-green-900 text-green-200' :
                        home_nba_momentum.possession_indicator === 'DEFENDING' ? 'bg-red-900 text-red-200' :
                        'bg-slate-700 ${textSecondary}'
                      }`}>
                        {home_nba_momentum.possession_indicator}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* NFL/NCAAF Momentum Bar (football only, live games) */}
      {(sportBadge === 'NFL' || sportBadge === 'NCAAF') && state.status === 'live' && ((home_nfl_momentum || away_nfl_momentum) || (home_ncaaf_momentum || away_ncaaf_momentum)) && (() => {
        const footballMomentum = sportBadge === 'NFL'
          ? { home: home_nfl_momentum, away: away_nfl_momentum }
          : { home: home_ncaaf_momentum, away: away_ncaaf_momentum };

        if (!footballMomentum.home && !footballMomentum.away) return null;

        return (
          <>
            {/* Momentum Bar */}
            <div className="mb-3">
              <div className={`text-base ${textLabel} mb-1`}>Game Momentum</div>
              <div className="flex items-center gap-2">
                <span className={`text-base ${textLabel} w-12`}>{state.away_team.name.split(' ').pop()}</span>
                <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden relative">
                  {(() => {
                    const awayMomentum = footballMomentum.away?.momentum_score || 50;
                    const homeMomentum = footballMomentum.home?.momentum_score || 50;
                    const awayPercent = (awayMomentum / (awayMomentum + homeMomentum)) * 100;
                    const homePercent = 100 - awayPercent;

                    return (
                      <>
                        <div
                          className="absolute left-0 top-0 h-full transition-all"
                          style={{ width: `${awayPercent}%`, backgroundColor: awayTeamColors.primary }}
                        />
                        <div
                          className="absolute right-0 top-0 h-full transition-all"
                          style={{ width: `${homePercent}%`, backgroundColor: homeTeamColors.primary }}
                        />
                        <div className="absolute left-1/2 top-0 h-full w-0.5 bg-white/30" style={{ transform: 'translateX(-50%)' }} />
                      </>
                    );
                  })()}
                </div>
                <span className={`text-base ${textLabel} w-12 text-right`}>{state.home_team.name.split(' ').pop()}</span>
              </div>
            </div>

            {/* Momentum Stats Panel */}
            <div className="mb-3 border border-orange-600/30 bg-orange-900/10 rounded p-2">
              <div className="text-base text-orange-400 font-semibold mb-2">Recent Momentum (Last ~6 Drives)</div>
              <div className="grid grid-cols-2 gap-3 text-base">
                {/* Away Team Momentum */}
                <div>
                  <div className={`${textLabel} font-semibold mb-1`}>{state.away_team.name.split(' ').pop()}</div>
                  {footballMomentum.away && (
                    <>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Momentum:</span>
                        <span className={`font-semibold ${
                          footballMomentum.away.momentum_score > 60 ? 'text-green-400' :
                          footballMomentum.away.momentum_score < 40 ? 'text-red-400' : `${textSecondary}`
                        }`}>{footballMomentum.away.momentum_score.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Yds/Play:</span>
                        <span className={
                          footballMomentum.home && footballMomentum.away.yards_per_play > footballMomentum.home.yards_per_play
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.away.yards_per_play.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Yards:</span>
                        <span className={
                          footballMomentum.home && footballMomentum.away.recent_yards > footballMomentum.home.recent_yards
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.away.recent_yards}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Points:</span>
                        <span className={
                          footballMomentum.home && footballMomentum.away.recent_points > footballMomentum.home.recent_points
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.away.recent_points}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>TDs:</span>
                        <span className={
                          footballMomentum.home && footballMomentum.away.touchdowns > footballMomentum.home.touchdowns
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.away.touchdowns}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>FGs:</span>
                        <span className={`${textSecondary}`}>{footballMomentum.away.field_goals}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Turnovers:</span>
                        <span className={
                          footballMomentum.home && footballMomentum.away.turnovers < footballMomentum.home.turnovers
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.away.turnovers}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`${textLabel}`}>Red Zone:</span>
                        <span className={`${textSecondary}`}>{footballMomentum.away.red_zone_efficiency}</span>
                      </div>
                      {footballMomentum.away.drive_state && (
                        <div className="mt-1">
                          <span className={`text-sm px-2 py-0.5 rounded ${
                            footballMomentum.away.drive_state === 'ATTACKING' ? 'bg-green-900 text-green-200' :
                            footballMomentum.away.drive_state === 'DEFENDING' ? 'bg-red-900 text-red-200' :
                            'bg-slate-700 ${textSecondary}'
                          }`}>
                            {footballMomentum.away.drive_state}
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Home Team Momentum */}
                <div>
                  <div className={`${textLabel} font-semibold mb-1`}>{state.home_team.name.split(' ').pop()}</div>
                  {footballMomentum.home && (
                    <>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Momentum:</span>
                        <span className={`font-semibold ${
                          footballMomentum.home.momentum_score > 60 ? 'text-green-400' :
                          footballMomentum.home.momentum_score < 40 ? 'text-red-400' : `${textSecondary}`
                        }`}>{footballMomentum.home.momentum_score.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Yds/Play:</span>
                        <span className={
                          footballMomentum.away && footballMomentum.home.yards_per_play > footballMomentum.away.yards_per_play
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.home.yards_per_play.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Yards:</span>
                        <span className={
                          footballMomentum.away && footballMomentum.home.recent_yards > footballMomentum.away.recent_yards
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.home.recent_yards}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Points:</span>
                        <span className={
                          footballMomentum.away && footballMomentum.home.recent_points > footballMomentum.away.recent_points
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.home.recent_points}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>TDs:</span>
                        <span className={
                          footballMomentum.away && footballMomentum.home.touchdowns > footballMomentum.away.touchdowns
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.home.touchdowns}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>FGs:</span>
                        <span className={`${textSecondary}`}>{footballMomentum.home.field_goals}</span>
                      </div>
                      <div className="flex justify-between mb-0.5">
                        <span className={`${textLabel}`}>Turnovers:</span>
                        <span className={
                          footballMomentum.away && footballMomentum.home.turnovers < footballMomentum.away.turnovers
                            ? 'text-green-400'
                            : `${textSecondary}`
                        }>{footballMomentum.home.turnovers}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`${textLabel}`}>Red Zone:</span>
                        <span className={`${textSecondary}`}>{footballMomentum.home.red_zone_efficiency}</span>
                      </div>
                      {footballMomentum.home.drive_state && (
                        <div className="mt-1">
                          <span className={`text-sm px-2 py-0.5 rounded ${
                            footballMomentum.home.drive_state === 'ATTACKING' ? 'bg-green-900 text-green-200' :
                            footballMomentum.home.drive_state === 'DEFENDING' ? 'bg-red-900 text-red-200' :
                            'bg-slate-700 ${textSecondary}'
                          }`}>
                            {footballMomentum.home.drive_state}
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          </>
        );
      })()}

      {/* Live Betting Lines (All Sports, Live Games) */}
      {state.status === 'live' && (state.away_team.money_line || state.home_team.money_line || state.away_team.spread || state.home_team.spread) && (
        <div className="mb-3 border border-yellow-600/30 bg-yellow-900/10 rounded p-3">
          <div className={`text-lg ${isNHL ? 'text-yellow-600' : 'text-yellow-400'} font-bold mb-2`}>Live Betting Lines</div>

          {/* Live Spreads */}
          {(state.away_team.spread !== null || state.home_team.spread !== null) && (
            <div className="mb-2">
              <div className={`text-base ${textLabel} mb-1`}>Spreads</div>
              <div className="flex justify-between text-base">
                <div className={textSecondary}>
                  <span className={textTertiary}>{state.away_team.name.split(' ').pop()}: </span>
                  <span className={`font-bold ${isNHL ? 'text-green-600' : 'text-green-400'}`}>
                    {state.away_team.spread !== null ? `${state.away_team.spread > 0 ? '+' : ''}${state.away_team.spread}` : 'N/A'}
                    {state.away_team.spread_price && <span className="text-sm"> ({state.away_team.spread_price > 0 ? '+' : ''}{state.away_team.spread_price})</span>}
                  </span>
                </div>
                <div className={textSecondary}>
                  <span className={textTertiary}>{state.home_team.name.split(' ').pop()}: </span>
                  <span className={`font-bold ${isNHL ? 'text-green-600' : 'text-green-400'}`}>
                    {state.home_team.spread !== null ? `${state.home_team.spread > 0 ? '+' : ''}${state.home_team.spread}` : 'N/A'}
                    {state.home_team.spread_price && <span className="text-sm"> ({state.home_team.spread_price > 0 ? '+' : ''}{state.home_team.spread_price})</span>}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Live Money Lines */}
          {(state.away_team.money_line !== null || state.home_team.money_line !== null) && (
            <div>
              <div className={`text-base ${textLabel} mb-1`}>Money Lines</div>
              <div className="flex justify-between text-base">
                <div className={textSecondary}>
                  <span className={textTertiary}>{state.away_team.name.split(' ').pop()}: </span>
                  <span className={`font-bold ${(state.away_team.money_line || 0) > 0 ? (isNHL ? 'text-blue-600' : 'text-blue-400') : textPrimary}`}>
                    {state.away_team.money_line !== null ? `${state.away_team.money_line > 0 ? '+' : ''}${state.away_team.money_line}` : 'N/A'}
                  </span>
                </div>
                <div className={textSecondary}>
                  <span className={textTertiary}>{state.home_team.name.split(' ').pop()}: </span>
                  <span className={`font-bold ${(state.home_team.money_line || 0) > 0 ? (isNHL ? 'text-blue-600' : 'text-blue-400') : textPrimary}`}>
                    {state.home_team.money_line !== null ? `${state.home_team.money_line > 0 ? '+' : ''}${state.home_team.money_line}` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* First Half Lines (All Sports, 1st half only) */}
      {state.status === 'live' && state.quarter && state.quarter <= 2 && (
        <div className="mb-3 border border-purple-600/30 bg-purple-900/10 rounded p-3">
          <div className="text-lg text-purple-400 font-bold mb-2">1st Half Lines</div>

          {/* First Half Total */}
          {projection.first_half_total && (
            <div className="mb-2">
              <div className={`text-base ${textLabel} font-semibold mb-1`}>Total</div>
              <div className="flex justify-between text-base">
                <div className={`${textSecondary}`}>
                  <span className={`${textLabel}`}>Current: </span>
                  <span className="font-bold text-white">{projection.first_half_current || 0}</span>
                </div>
                <div className={`${textSecondary}`}>
                  <span className={`${textLabel}`}>Projected: </span>
                  <span className="font-bold text-purple-300">{projection.first_half_total.toFixed(1)}</span>
                </div>
              </div>
            </div>
          )}

          {/* First Half Spreads */}
          {(state.away_team.spread !== null || state.home_team.spread !== null) && (
            <div className="mb-2">
              <div className={`text-base ${textLabel} font-semibold mb-1`}>Spreads</div>
              <div className="flex justify-between text-base">
                <div className={`${textSecondary}`}>
                  <span className={`${textLabel}`}>{state.away_team.name.split(' ').pop()}: </span>
                  <span className="font-bold text-green-400">
                    {state.away_team.spread !== null ? `${state.away_team.spread > 0 ? '+' : ''}${(state.away_team.spread / 2).toFixed(1)}` : 'N/A'}
                    {state.away_team.spread_price && <span className="text-sm"> ({state.away_team.spread_price > 0 ? '+' : ''}{state.away_team.spread_price})</span>}
                  </span>
                </div>
                <div className={`${textSecondary}`}>
                  <span className={`${textLabel}`}>{state.home_team.name.split(' ').pop()}: </span>
                  <span className="font-bold text-green-400">
                    {state.home_team.spread !== null ? `${state.home_team.spread > 0 ? '+' : ''}${(state.home_team.spread / 2).toFixed(1)}` : 'N/A'}
                    {state.home_team.spread_price && <span className="text-sm"> ({state.home_team.spread_price > 0 ? '+' : ''}{state.home_team.spread_price})</span>}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* First Half Money Lines */}
          {(state.away_team.money_line !== null || state.home_team.money_line !== null) && (
            <div>
              <div className={`text-base ${textLabel} font-semibold mb-1`}>Money Lines</div>
              <div className="flex justify-between text-base">
                <div className={`${textSecondary}`}>
                  <span className={`${textLabel}`}>{state.away_team.name.split(' ').pop()}: </span>
                  <span className={`font-bold ${(state.away_team.money_line || 0) > 0 ? 'text-blue-400' : 'text-white'}`}>
                    {state.away_team.money_line !== null ? `${state.away_team.money_line > 0 ? '+' : ''}${state.away_team.money_line}` : 'N/A'}
                  </span>
                </div>
                <div className={`${textSecondary}`}>
                  <span className={`${textLabel}`}>{state.home_team.name.split(' ').pop()}: </span>
                  <span className={`font-bold ${(state.home_team.money_line || 0) > 0 ? 'text-blue-400' : 'text-white'}`}>
                    {state.home_team.money_line !== null ? `${state.home_team.money_line > 0 ? '+' : ''}${state.home_team.money_line}` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* NHL Momentum Bar (NHL only, live games) */}
      {sportBadge === 'NHL' && state.status === 'live' && (away_nhl_momentum || home_nhl_momentum) && (
        <div className="mb-3">
          <div className={`text-base ${textLabel} mb-1`}>Game Momentum</div>
          <div className="flex items-center gap-2">
            <span className={`text-base ${textLabel} w-12`}>{state.away_team.name.split(' ').pop()}</span>
            <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden relative">
              {/* Calculate momentum percentage (0-100 scale for each team) */}
              {(() => {
                const awayMomentum = away_nhl_momentum?.momentum_score || 50;
                const homeMomentum = home_nhl_momentum?.momentum_score || 50;
                const totalMomentum = awayMomentum + homeMomentum;
                const awayPercent = totalMomentum !== 0 ? (awayMomentum / totalMomentum) * 100 : 50;
                const homePercent = 100 - awayPercent;

                return (
                  <>
                    <div
                      className="absolute left-0 top-0 h-full transition-all bg-cyan-500"
                      style={{ width: `${awayPercent}%` }}
                    />
                    <div
                      className="absolute right-0 top-0 h-full transition-all bg-orange-500"
                      style={{ width: `${homePercent}%` }}
                    />
                    {/* Center line */}
                    <div className="absolute left-1/2 top-0 h-full w-0.5 bg-white/30" style={{ transform: 'translateX(-50%)' }} />
                  </>
                );
              })()}
            </div>
            <span className={`text-base ${textLabel} w-12 text-right`}>{state.home_team.name.split(' ').pop()}</span>
          </div>
        </div>
      )}

      {/* NHL Momentum Stats (NHL only, live games) */}
      {sportBadge === 'NHL' && state.status === 'live' && (away_nhl_momentum || home_nhl_momentum) && (
        <div className="mb-3 border border-cyan-600/30 bg-cyan-900/10 rounded p-2">
          <div className="text-base text-cyan-400 font-semibold mb-2">Recent Momentum (Last 5 Min)</div>
          <div className="grid grid-cols-2 gap-3 text-base">
            {/* Away Team Momentum */}
            <div>
              <div className={`${textLabel} font-semibold mb-1`}>{state.away_team.name.split(' ').pop()}</div>
              {away_nhl_momentum && (
                <>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Momentum:</span>
                    <span className={`font-semibold ${
                      away_nhl_momentum.momentum_score > 60 ? 'text-green-400' :
                      away_nhl_momentum.momentum_score < 40 ? 'text-red-400' : `${textSecondary}`
                    }`}>{away_nhl_momentum.momentum_score.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Shots:</span>
                    <span className={
                      home_nhl_momentum && away_nhl_momentum.recent_shots > home_nhl_momentum.recent_shots
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nhl_momentum.recent_shots}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Chances:</span>
                    <span className={
                      home_nhl_momentum && away_nhl_momentum.scoring_chances > home_nhl_momentum.scoring_chances
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nhl_momentum.scoring_chances}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Faceoffs:</span>
                    <span className={
                      home_nhl_momentum && away_nhl_momentum.faceoff_wins > home_nhl_momentum.faceoff_wins
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nhl_momentum.faceoff_wins}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Zone Events:</span>
                    <span className={
                      home_nhl_momentum && away_nhl_momentum.offensive_zone_events > home_nhl_momentum.offensive_zone_events
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nhl_momentum.offensive_zone_events}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>PP Opps:</span>
                    <span className={`${textSecondary}`}>{away_nhl_momentum.power_play_opps || '0/0'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={`${textLabel}`}>PIM:</span>
                    <span className={
                      home_nhl_momentum && (away_nhl_momentum.penalty_minutes || 0) < (home_nhl_momentum.penalty_minutes || 0)
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{away_nhl_momentum.penalty_minutes || 0}</span>
                  </div>
                  {away_nhl_momentum.possession_indicator && (
                    <div className="mt-1">
                      <span className={`text-sm px-2 py-0.5 rounded ${
                        away_nhl_momentum.possession_indicator === 'ATTACKING' ? 'bg-green-900 text-green-200' :
                        away_nhl_momentum.possession_indicator === 'DEFENDING' ? 'bg-red-900 text-red-200' :
                        'bg-slate-700 ${textSecondary}'
                      }`}>
                        {away_nhl_momentum.possession_indicator}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Home Team Momentum */}
            <div>
              <div className={`${textLabel} font-semibold mb-1`}>{state.home_team.name.split(' ').pop()}</div>
              {home_nhl_momentum && (
                <>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Momentum:</span>
                    <span className={`font-semibold ${
                      home_nhl_momentum.momentum_score > 60 ? 'text-green-400' :
                      home_nhl_momentum.momentum_score < 40 ? 'text-red-400' : `${textSecondary}`
                    }`}>{home_nhl_momentum.momentum_score.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Shots:</span>
                    <span className={
                      away_nhl_momentum && home_nhl_momentum.recent_shots > away_nhl_momentum.recent_shots
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nhl_momentum.recent_shots}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Chances:</span>
                    <span className={
                      away_nhl_momentum && home_nhl_momentum.scoring_chances > away_nhl_momentum.scoring_chances
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nhl_momentum.scoring_chances}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Faceoffs:</span>
                    <span className={
                      away_nhl_momentum && home_nhl_momentum.faceoff_wins > away_nhl_momentum.faceoff_wins
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nhl_momentum.faceoff_wins}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>Zone Events:</span>
                    <span className={
                      away_nhl_momentum && home_nhl_momentum.offensive_zone_events > away_nhl_momentum.offensive_zone_events
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nhl_momentum.offensive_zone_events}</span>
                  </div>
                  <div className="flex justify-between mb-0.5">
                    <span className={`${textLabel}`}>PP Opps:</span>
                    <span className={`${textSecondary}`}>{home_nhl_momentum.power_play_opps || '0/0'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={`${textLabel}`}>PIM:</span>
                    <span className={
                      away_nhl_momentum && (home_nhl_momentum.penalty_minutes || 0) < (away_nhl_momentum.penalty_minutes || 0)
                        ? 'text-green-400'
                        : `${textSecondary}`
                    }>{home_nhl_momentum.penalty_minutes || 0}</span>
                  </div>
                  {home_nhl_momentum.possession_indicator && (
                    <div className="mt-1">
                      <span className={`text-sm px-2 py-0.5 rounded ${
                        home_nhl_momentum.possession_indicator === 'ATTACKING' ? 'bg-green-900 text-green-200' :
                        home_nhl_momentum.possession_indicator === 'DEFENDING' ? 'bg-red-900 text-red-200' :
                        'bg-slate-700 ${textSecondary}'
                      }`}>
                        {home_nhl_momentum.possession_indicator}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* NHL Season Stats Section */}
      {sportBadge === 'NHL' && (away_nhl_stats || home_nhl_stats) && (
        <div className={`mb-3 ${dividerClass} pt-3`}>
          <div className="mb-3">
            <div className={`text-base ${textLabel} mb-2`}>NHL Season Stats</div>
            <div className="flex gap-2">
              <button
                onClick={() => setStatsView('stats')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'stats'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Stats
              </button>
              <button
                onClick={() => setStatsView('rankings')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'rankings'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Ranks
              </button>
              <button
                onClick={() => setStatsView('combined')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'combined'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Both
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-base">
            {/* Away Team Stats */}
            <div className="space-y-1">
              <div className={`${textHeader} font-bold mb-2 text-center text-base`}>{state.away_team.name}</div>
              {away_nhl_stats && (
                <>
                  {(statsView === 'stats' || statsView === 'combined') && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Record:</span>
                        <span className={`font-semibold ${
                          home_nhl_stats && away_nhl_stats.win_pct > home_nhl_stats.win_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_nhl_stats.wins}-{away_nhl_stats.losses}-{away_nhl_stats.ot_losses}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Points:</span>
                        <span className={
                          home_nhl_stats && away_nhl_stats.points > home_nhl_stats.points
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_nhl_stats.points}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GF/G:</span>
                        <span className={
                          home_nhl_stats && away_nhl_stats.goals_per_game > home_nhl_stats.goals_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_nhl_stats.goals_per_game.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GA/G:</span>
                        <span className={
                          home_nhl_stats && away_nhl_stats.goals_against_per_game < home_nhl_stats.goals_against_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_nhl_stats.goals_against_per_game.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PP%:</span>
                        <span className={
                          home_nhl_stats && away_nhl_stats.power_play_pct > home_nhl_stats.power_play_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(away_nhl_stats.power_play_pct * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PK%:</span>
                        <span className={
                          home_nhl_stats && away_nhl_stats.penalty_kill_pct > home_nhl_stats.penalty_kill_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(away_nhl_stats.penalty_kill_pct * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>SV%:</span>
                        <span className={
                          home_nhl_stats && away_nhl_stats.save_pct > home_nhl_stats.save_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(away_nhl_stats.save_pct * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Shots/G:</span>
                        <span className={
                          home_nhl_stats && away_nhl_stats.shots_per_game > home_nhl_stats.shots_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_nhl_stats.shots_per_game.toFixed(1)}</span>
                      </div>
                      {away_nhl_stats.form_trend && (
                        <div className="flex items-center justify-between">
                          <span className={`${textLabel}`}>Form:</span>
                          <span className={`px-1 py-0.5 rounded text-sm ${
                            away_nhl_stats.form_trend === 'HOT' ? 'bg-green-900 text-green-200' :
                            away_nhl_stats.form_trend === 'COLD' ? 'bg-red-900 text-red-200' :
                            'bg-slate-700 ${textSecondary}'
                          }`}>{away_nhl_stats.form_trend}</span>
                        </div>
                      )}
                    </>
                  )}
                  {(statsView === 'rankings' || statsView === 'combined') && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GF/G Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.goals_per_game_rank || 32)}`}>#{away_nhl_stats.goals_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GA/G Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.goals_against_per_game_rank || 32)}`}>#{away_nhl_stats.goals_against_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Shots/G Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.shots_per_game_rank || 32)}`}>#{away_nhl_stats.shots_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>SA/G Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.shots_against_per_game_rank || 32)}`}>#{away_nhl_stats.shots_against_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PP% Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.power_play_pct_rank || 32)}`}>#{away_nhl_stats.power_play_pct_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PK% Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.penalty_kill_pct_rank || 32)}`}>#{away_nhl_stats.penalty_kill_pct_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>SV% Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.save_pct_rank || 32)}`}>#{away_nhl_stats.save_pct_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PDO Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nhl_stats.pdo_rank || 32)}`}>#{away_nhl_stats.pdo_rank || 'N/A'}</span>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>

            {/* Home Team Stats */}
            <div className="space-y-1">
              <div className={`${textHeader} font-bold mb-2 text-center text-base`}>{state.home_team.name}</div>
              {home_nhl_stats && (
                <>
                  {(statsView === 'stats' || statsView === 'combined') && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Record:</span>
                        <span className={`font-semibold ${
                          away_nhl_stats && home_nhl_stats.win_pct > away_nhl_stats.win_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_nhl_stats.wins}-{home_nhl_stats.losses}-{home_nhl_stats.ot_losses}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Points:</span>
                        <span className={
                          away_nhl_stats && home_nhl_stats.points > away_nhl_stats.points
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_nhl_stats.points}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GF/G:</span>
                        <span className={
                          away_nhl_stats && home_nhl_stats.goals_per_game > away_nhl_stats.goals_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_nhl_stats.goals_per_game.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GA/G:</span>
                        <span className={
                          away_nhl_stats && home_nhl_stats.goals_against_per_game < away_nhl_stats.goals_against_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_nhl_stats.goals_against_per_game.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PP%:</span>
                        <span className={
                          away_nhl_stats && home_nhl_stats.power_play_pct > away_nhl_stats.power_play_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(home_nhl_stats.power_play_pct * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PK%:</span>
                        <span className={
                          away_nhl_stats && home_nhl_stats.penalty_kill_pct > away_nhl_stats.penalty_kill_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(home_nhl_stats.penalty_kill_pct * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>SV%:</span>
                        <span className={
                          away_nhl_stats && home_nhl_stats.save_pct > away_nhl_stats.save_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(home_nhl_stats.save_pct * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Shots/G:</span>
                        <span className={
                          away_nhl_stats && home_nhl_stats.shots_per_game > away_nhl_stats.shots_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_nhl_stats.shots_per_game.toFixed(1)}</span>
                      </div>
                      {home_nhl_stats.form_trend && (
                        <div className="flex items-center justify-between">
                          <span className={`${textLabel}`}>Form:</span>
                          <span className={`px-1 py-0.5 rounded text-sm ${
                            home_nhl_stats.form_trend === 'HOT' ? 'bg-green-900 text-green-200' :
                            home_nhl_stats.form_trend === 'COLD' ? 'bg-red-900 text-red-200' :
                            'bg-slate-700 ${textSecondary}'
                          }`}>{home_nhl_stats.form_trend}</span>
                        </div>
                      )}
                    </>
                  )}
                  {(statsView === 'rankings' || statsView === 'combined') && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GF/G Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.goals_per_game_rank || 32)}`}>#{home_nhl_stats.goals_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>GA/G Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.goals_against_per_game_rank || 32)}`}>#{home_nhl_stats.goals_against_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Shots/G Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.shots_per_game_rank || 32)}`}>#{home_nhl_stats.shots_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>SA/G Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.shots_against_per_game_rank || 32)}`}>#{home_nhl_stats.shots_against_per_game_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PP% Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.power_play_pct_rank || 32)}`}>#{home_nhl_stats.power_play_pct_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PK% Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.penalty_kill_pct_rank || 32)}`}>#{home_nhl_stats.penalty_kill_pct_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>SV% Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.save_pct_rank || 32)}`}>#{home_nhl_stats.save_pct_rank || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PDO Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nhl_stats.pdo_rank || 32)}`}>#{home_nhl_stats.pdo_rank || 'N/A'}</span>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* NFL Season Stats Section */}
      {(sportBadge === 'NFL' || sportBadge === 'NCAAF') && (away_nfl_stats || home_nfl_stats) && (
        <div className={`mb-3 ${dividerClass} pt-3`}>
          {/* Stats View Toggle */}
          <div className="mb-3">
            <div className={`text-base ${textLabel} mb-2`}>Season Stats</div>
            <div className="flex gap-2">
              <button
                onClick={() => setStatsView('stats')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'stats'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Stats
              </button>
              <button
                onClick={() => setStatsView('rankings')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'rankings'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Ranks
              </button>
              <button
                onClick={() => setStatsView('combined')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'combined'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Both
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-base">
            {/* Away Team Stats */}
            <div className="space-y-1">
              <div className={`${textHeader} font-bold mb-2 text-center text-base`}>{state.away_team.name}</div>
              {away_nfl_stats && (
                <>
                  {/* RANKINGS VIEW - Show only rankings */}
                  {statsView === 'rankings' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Off Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nfl_stats.points_per_game_rank || 32)}`}>
                          #{away_nfl_stats.points_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Def Rank:</span>
                        <span className={`font-bold ${getRankColor(away_nfl_stats.points_allowed_per_game_rank || 32)}`}>
                          #{away_nfl_stats.points_allowed_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pass Off:</span>
                        <span className={`font-bold ${getRankColor(away_nfl_stats.passing_yards_per_game_rank || 32)}`}>
                          #{away_nfl_stats.passing_yards_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Rush Off:</span>
                        <span className={`font-bold ${getRankColor(away_nfl_stats.rushing_yards_per_game_rank || 32)}`}>
                          #{away_nfl_stats.rushing_yards_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>TO Margin:</span>
                        <span className={`font-bold ${getRankColor(away_nfl_stats.turnover_differential_rank || 32)}`}>
                          #{away_nfl_stats.turnover_differential_rank || 'N/A'}
                        </span>
                      </div>
                    </>
                  )}

                  {/* COMBINED VIEW - Show stats with rankings */}
                  {statsView === 'combined' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.points_per_game > home_nfl_stats.points_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_nfl_stats.points_per_game.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_nfl_stats.points_per_game_rank || 32)}`}>
                            (#{away_nfl_stats.points_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PA/G:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.points_allowed_per_game < home_nfl_stats.points_allowed_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_nfl_stats.points_allowed_per_game.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_nfl_stats.points_allowed_per_game_rank || 32)}`}>
                            (#{away_nfl_stats.points_allowed_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pass YPG:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.passing_yards_per_game > home_nfl_stats.passing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_nfl_stats.passing_yards_per_game.toFixed(0)}
                          <span className={`text-sm ml-1 ${getRankColor(away_nfl_stats.passing_yards_per_game_rank || 32)}`}>
                            (#{away_nfl_stats.passing_yards_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Rush YPG:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.rushing_yards_per_game > home_nfl_stats.rushing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_nfl_stats.rushing_yards_per_game.toFixed(0)}
                          <span className={`text-sm ml-1 ${getRankColor(away_nfl_stats.rushing_yards_per_game_rank || 32)}`}>
                            (#{away_nfl_stats.rushing_yards_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>TO Diff:</span>
                        <span className={`font-bold ${
                          away_nfl_stats.turnover_differential > 0 ? 'text-green-400' :
                          away_nfl_stats.turnover_differential < 0 ? 'text-red-400' : `${textValue}`
                        }`}>
                          {away_nfl_stats.turnover_differential > 0 ? '+' : ''}{away_nfl_stats.turnover_differential.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_nfl_stats.turnover_differential_rank || 32)}`}>
                            (#{away_nfl_stats.turnover_differential_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                    </>
                  )}

                  {/* STATS VIEW (DEFAULT) - Show only stats */}
                  {statsView === 'stats' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Record:</span>
                        <span className={`font-semibold ${
                          home_nfl_stats && away_nfl_stats.win_pct > home_nfl_stats.win_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_nfl_stats.wins}-{away_nfl_stats.losses}{away_nfl_stats.ties > 0 ? `-${away_nfl_stats.ties}` : ''}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.points_per_game > home_nfl_stats.points_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_nfl_stats.points_per_game.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PA/G:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.points_allowed_per_game < home_nfl_stats.points_allowed_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_nfl_stats.points_allowed_per_game.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Yards/G:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.total_yards_per_game > home_nfl_stats.total_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_nfl_stats.total_yards_per_game.toFixed(0)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pass YPG:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.passing_yards_per_game > home_nfl_stats.passing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_nfl_stats.passing_yards_per_game.toFixed(0)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Rush YPG:</span>
                        <span className={`font-bold ${
                          home_nfl_stats && away_nfl_stats.rushing_yards_per_game > home_nfl_stats.rushing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_nfl_stats.rushing_yards_per_game.toFixed(0)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>TO Diff:</span>
                        <span className={`font-bold ${
                          away_nfl_stats.turnover_differential > 0 ? 'text-green-400' :
                          away_nfl_stats.turnover_differential < 0 ? 'text-red-400' : `${textValue}`
                        }`}>{away_nfl_stats.turnover_differential > 0 ? '+' : ''}{away_nfl_stats.turnover_differential.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>3rd Down:</span>
                        <span className={`font-bold ${
                      home_nfl_stats && away_nfl_stats.third_down_pct > home_nfl_stats.third_down_pct
                        ? 'text-green-400'
                        : `${textValue}`
                    }`}>{(away_nfl_stats.third_down_pct * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`${textLabel}`}>Red Zone:</span>
                    <span className={`font-bold ${
                      home_nfl_stats && away_nfl_stats.red_zone_pct > home_nfl_stats.red_zone_pct
                        ? 'text-green-400'
                        : `${textValue}`
                    }`}>{(away_nfl_stats.red_zone_pct * 100).toFixed(1)}%</span>
                  </div>
                  {away_nfl_stats.form_trend && (
                    <div className="flex items-center justify-between">
                      <span className={`${textLabel}`}>Form:</span>
                      <span className={`px-1 py-0.5 rounded text-sm ${
                        away_nfl_stats.form_trend === 'HOT' ? 'bg-green-900 text-green-200' :
                        away_nfl_stats.form_trend === 'COLD' ? 'bg-red-900 text-red-200' :
                        'bg-slate-700 ${textSecondary}'
                      }`}>{away_nfl_stats.form_trend}</span>
                    </div>
                  )}
                </>
              )}
                </>
              )}
            </div>

            {/* Home Team Stats */}
            <div className="space-y-1">
              <div className={`${textHeader} font-bold mb-2 text-center text-base`}>{state.home_team.name}</div>
              {home_nfl_stats && (
                <>
                  {/* RANKINGS VIEW - Show only rankings */}
                  {statsView === 'rankings' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Off Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nfl_stats.points_per_game_rank || 32)}`}>
                          #{home_nfl_stats.points_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Def Rank:</span>
                        <span className={`font-bold ${getRankColor(home_nfl_stats.points_allowed_per_game_rank || 32)}`}>
                          #{home_nfl_stats.points_allowed_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pass Off:</span>
                        <span className={`font-bold ${getRankColor(home_nfl_stats.passing_yards_per_game_rank || 32)}`}>
                          #{home_nfl_stats.passing_yards_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Rush Off:</span>
                        <span className={`font-bold ${getRankColor(home_nfl_stats.rushing_yards_per_game_rank || 32)}`}>
                          #{home_nfl_stats.rushing_yards_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>TO Margin:</span>
                        <span className={`font-bold ${getRankColor(home_nfl_stats.turnover_differential_rank || 32)}`}>
                          #{home_nfl_stats.turnover_differential_rank || 'N/A'}
                        </span>
                      </div>
                    </>
                  )}

                  {/* COMBINED VIEW - Show stats with rankings */}
                  {statsView === 'combined' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.points_per_game > away_nfl_stats.points_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_nfl_stats.points_per_game.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_nfl_stats.points_per_game_rank || 32)}`}>
                            (#{home_nfl_stats.points_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PA/G:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.points_allowed_per_game < away_nfl_stats.points_allowed_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_nfl_stats.points_allowed_per_game.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_nfl_stats.points_allowed_per_game_rank || 32)}`}>
                            (#{home_nfl_stats.points_allowed_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pass YPG:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.passing_yards_per_game > away_nfl_stats.passing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_nfl_stats.passing_yards_per_game.toFixed(0)}
                          <span className={`text-sm ml-1 ${getRankColor(home_nfl_stats.passing_yards_per_game_rank || 32)}`}>
                            (#{home_nfl_stats.passing_yards_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Rush YPG:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.rushing_yards_per_game > away_nfl_stats.rushing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_nfl_stats.rushing_yards_per_game.toFixed(0)}
                          <span className={`text-sm ml-1 ${getRankColor(home_nfl_stats.rushing_yards_per_game_rank || 32)}`}>
                            (#{home_nfl_stats.rushing_yards_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>TO Diff:</span>
                        <span className={`font-bold ${
                          home_nfl_stats.turnover_differential > 0 ? 'text-green-400' :
                          home_nfl_stats.turnover_differential < 0 ? 'text-red-400' : `${textValue}`
                        }`}>
                          {home_nfl_stats.turnover_differential > 0 ? '+' : ''}{home_nfl_stats.turnover_differential.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_nfl_stats.turnover_differential_rank || 32)}`}>
                            (#{home_nfl_stats.turnover_differential_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                    </>
                  )}

                  {/* STATS VIEW (DEFAULT) - Show only stats */}
                  {statsView === 'stats' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Record:</span>
                        <span className={`font-semibold ${
                          away_nfl_stats && home_nfl_stats.win_pct > away_nfl_stats.win_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_nfl_stats.wins}-{home_nfl_stats.losses}{home_nfl_stats.ties > 0 ? `-${home_nfl_stats.ties}` : ''}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.points_per_game > away_nfl_stats.points_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_nfl_stats.points_per_game.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PA/G:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.points_allowed_per_game < away_nfl_stats.points_allowed_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_nfl_stats.points_allowed_per_game.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Yards/G:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.total_yards_per_game > away_nfl_stats.total_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_nfl_stats.total_yards_per_game.toFixed(0)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pass YPG:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.passing_yards_per_game > away_nfl_stats.passing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_nfl_stats.passing_yards_per_game.toFixed(0)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Rush YPG:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.rushing_yards_per_game > away_nfl_stats.rushing_yards_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_nfl_stats.rushing_yards_per_game.toFixed(0)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>TO Diff:</span>
                        <span className={`font-bold ${
                          home_nfl_stats.turnover_differential > 0 ? 'text-green-400' :
                          home_nfl_stats.turnover_differential < 0 ? 'text-red-400' : `${textValue}`
                        }`}>{home_nfl_stats.turnover_differential > 0 ? '+' : ''}{home_nfl_stats.turnover_differential.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>3rd Down:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.third_down_pct > away_nfl_stats.third_down_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{(home_nfl_stats.third_down_pct * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Red Zone:</span>
                        <span className={`font-bold ${
                          away_nfl_stats && home_nfl_stats.red_zone_pct > away_nfl_stats.red_zone_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{(home_nfl_stats.red_zone_pct * 100).toFixed(1)}%</span>
                      </div>
                      {home_nfl_stats.form_trend && (
                        <div className="flex items-center justify-between">
                          <span className={`${textLabel}`}>Form:</span>
                          <span className={`px-1 py-0.5 rounded text-sm ${
                            home_nfl_stats.form_trend === 'HOT' ? 'bg-green-900 text-green-200' :
                            home_nfl_stats.form_trend === 'COLD' ? 'bg-red-900 text-red-200' :
                            'bg-slate-700 ${textSecondary}'
                          }`}>{home_nfl_stats.form_trend}</span>
                        </div>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Odds Summary */}
      <div className={`${dividerClass} pt-3 space-y-2`}>
        <div className="flex justify-between text-base">
          <span className={`${textLabel}`}>Pregame Total (FD):</span>
          <span className="font-bold text-white">{Math.round(projection.pregame_total)}</span>
        </div>
        <div className="flex justify-between text-base">
          <span className={`${textLabel}`}>Current Live Avg:</span>
          <span className="font-bold text-white">{avgTotal}</span>
        </div>
        {projection.line_movement !== null && projection.line_movement !== undefined && (
          <div className="flex justify-between text-base">
            <span className={`${textLabel}`}>Line Movement:</span>
            <span className={`font-bold ${projection.line_movement > 0 ? 'text-green-400' : projection.line_movement < 0 ? 'text-red-400' : 'text-white'}`}>
              {projection.line_movement > 0 ? '+' : ''}{projection.line_movement.toFixed(1)}
            </span>
          </div>
        )}
        {projection.best_book_disparity && projection.best_disparity_amount && (
          <div className="flex justify-between text-base">
            <span className={`${textLabel}`}>Biggest Outlier:</span>
            <span className="font-bold text-yellow-400">{projection.best_book_disparity} (<span className="font-bold">{projection.best_disparity_amount.toFixed(1)}</span>)</span>
          </div>
        )}
      </div>

      {/* Projection (only for live games) */}
      {state.status === 'live' && projection.projected_final > 0 && (
        <div className={`${dividerClass} mt-3 pt-3 space-y-2`}>
          <div className="flex justify-between text-base">
            <span className={`${textLabel}`}>Projected:</span>
            <span className="font-bold text-blue-400">{projection.projected_final.toFixed(1)}</span>
          </div>
          {projection.edge !== null && (
            <div className="flex justify-between text-base">
              <span className={`${textLabel}`}>Edge:</span>
              <span className={`font-bold ${
                Math.abs(projection.edge) >= 5
                  ? projection.edge > 0 ? 'text-green-400' : 'text-red-400'
                  : `${textSecondary}`
              }`}>
                {projection.edge > 0 ? '+' : ''}{projection.edge.toFixed(1)}
              </span>
            </div>
          )}
          {projection.pace_indicator && (
            <div className="flex justify-between text-base">
              <span className={`${textLabel}`}>Pace:</span>
              <span className={`${textSecondary}`}>{projection.pace_indicator}</span>
            </div>
          )}
          {projection.strength_factor !== null && projection.strength_factor !== undefined && (
            <div className="flex justify-between text-base">
              <span className={`${textLabel}`}>Strength:</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      projection.strength_factor >= 70 ? 'bg-green-500' :
                      projection.strength_factor >= 50 ? 'bg-yellow-500' :
                      projection.strength_factor >= 30 ? 'bg-orange-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(100, projection.strength_factor)}%` }}
                  />
                </div>
                <span className={`font-bold ${
                  projection.strength_factor >= 70 ? 'text-green-400' :
                  projection.strength_factor >= 50 ? 'text-yellow-400' :
                  projection.strength_factor >= 30 ? 'text-orange-400' : 'text-red-400'
                }`}>
                  {projection.strength_factor.toFixed(1)}
                </span>
              </div>
            </div>
          )}
          {projection.unit_recommendation !== null && projection.unit_recommendation !== undefined && projection.unit_recommendation > 0 && (
            <div className="flex justify-between text-base">
              <span className={`${textLabel}`}>Bet Size:</span>
              <span className="font-bold text-purple-400">{projection.unit_recommendation.toFixed(1)} units</span>
            </div>
          )}
          {projection.recommendation && (
            <div className={`text-center font-bold text-lg py-2 rounded ${
              projection.recommendation === 'OVER'
                ? 'bg-green-900 text-green-200'
                : 'bg-red-900 text-red-200'
            }`}>
              BET {projection.recommendation}
            </div>
          )}
        </div>
      )}

      {/* All Odds with Latency */}
      {odds.length > 0 && (
        <div className={`${dividerClass} mt-3 pt-3`}>
          {/* Market Type Tabs */}
          <div className="flex gap-2 mb-3">
            <button
              onClick={() => setSelectedMarket('spread')}
              className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                selectedMarket === 'spread'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Spread
            </button>
            <button
              onClick={() => setSelectedMarket('moneyline')}
              className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                selectedMarket === 'moneyline'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Moneyline
            </button>
            <button
              onClick={() => setSelectedMarket('totals')}
              className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                selectedMarket === 'totals'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Totals
            </button>
          </div>

          {/* Section Header */}
          <div className={`text-base ${textLabel} mb-2`}>
            {selectedMarket === 'totals' && (
              <>
                Sportsbook Lines & Speed (Best Overs ↑ / Best Unders ↓)
                <div className={`text-sm ${textMuted} mt-0.5`}>Latency times are approximate and vary by sport</div>
              </>
            )}
            {selectedMarket === 'spread' && (
              <>
                Sportsbook Spreads & Speed
                <div className={`text-sm ${textMuted} mt-0.5`}>Latency times are approximate and vary by sport</div>
              </>
            )}
            {selectedMarket === 'moneyline' && (
              <>
                Sportsbook Moneylines & Speed
                <div className={`text-sm ${textMuted} mt-0.5`}>Latency times are approximate and vary by sport</div>
              </>
            )}
          </div>
          <div className="space-y-1">
            {(() => {
              // Deduplicate odds by bookmaker (keep first occurrence)
              const uniqueOdds = odds.filter((odd, index, self) =>
                index === self.findIndex((o) => o.bookmaker === odd.bookmaker)
              );

              // Find min and max latency across all books
              const latencies = uniqueOdds.map(o => o.latency_ms).filter(l => l !== null && l !== undefined) as number[];
              const minLatency = latencies.length > 0 ? Math.min(...latencies) : null;
              const maxLatency = latencies.length > 0 ? Math.max(...latencies) : null;

              return uniqueOdds.map((odd, idx) => {
                // Determine if this book should be highlighted based on recommendation
                const shouldHighlight = projection.recommendation && (
                  (projection.recommendation === 'OVER' && odd.is_best_over) ||
                  (projection.recommendation === 'UNDER' && odd.is_best_under)
                );

                // Only highlight fastest (red) and slowest (green)
                const getLatencyColor = (latencyMs: number | null) => {
                  if (latencyMs === null || latencyMs === undefined) return `${textLabel}`;
                  if (minLatency !== null && latencyMs === minLatency) return isNHL ? 'text-red-600' : 'text-red-400'; // Fastest = worst
                  if (maxLatency !== null && latencyMs === maxLatency && maxLatency > minLatency) return isNHL ? 'text-green-600' : 'text-green-400'; // Slowest = best
                  return `${textLabel}`; // Everything else neutral
                };

                // Format latency for display
                const formatLatency = (latencyMs: number | null) => {
                  if (latencyMs === null || latencyMs === undefined) return '';
                  if (latencyMs === 0) return '~0s';
                  if (latencyMs < 1000) return '~<1s';
                  const seconds = Math.round(latencyMs / 1000);
                  return `~${seconds}s`;
                };

                // Only show edge for slowest book
                const getBettorEdge = (latencyMs: number | null) => {
                  if (latencyMs === null || latencyMs === undefined) return '';
                  if (maxLatency === null || latencyMs !== maxLatency || maxLatency === minLatency) return '';

                  // Calculate edge based on actual delay
                  if (maxLatency < 5000) return '(+0.5%)';
                  if (maxLatency < 15000) return '(+1.5%)';
                  return '(+3%)';
                };

                const bookmakerInfo = getBookmakerInfo(odd.bookmaker);

                // Get bookmaker URL for clickable link
                const normalizedKey = odd.bookmaker
                  .toLowerCase()
                  .replace(/\s+/g, '')
                  .replace(/\./g, '')
                  .replace(/_/g, '');
                const bookmakerData = BOOKMAKERS[normalizedKey];

                // Try to get game-specific URL first, fallback to generic sport URL
                const gameSpecificUrl = getGameSpecificUrl(
                  normalizedKey,
                  state.home_team.name,
                  state.away_team.name,
                  state.sport_key,
                  state.commence_time
                );
                const bookmakerUrl = gameSpecificUrl || bookmakerData?.url || '#';

                return (
                  <div
                    key={idx}
                    className={`flex justify-between items-center text-base p-1 rounded ${
                      shouldHighlight ? 'bg-blue-900/50 border border-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {bookmakerInfo.logo ? (
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            handleBookmakerClick(odd.bookmaker, odd, bookmakerUrl);
                          }}
                          className="inline-block hover:opacity-70 transition-opacity cursor-pointer border-0 bg-transparent p-0"
                          title={`Track bet & visit ${odd.bookmaker}`}
                        >
                          <img
                            src={bookmakerInfo.logo}
                            alt={odd.bookmaker}
                            className="w-5 h-5 object-contain"
                            onError={(e) => e.currentTarget.style.display = 'none'}
                          />
                        </button>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            handleBookmakerClick(odd.bookmaker, odd, bookmakerUrl);
                          }}
                          className="inline-block hover:opacity-70 transition-opacity cursor-pointer border-0 bg-transparent p-0"
                          title={`Track bet & visit ${odd.bookmaker}`}
                        >
                          <span className={`px-2 py-0.5 rounded font-bold text-base ${bookmakerInfo.bg} ${bookmakerInfo.text}`}>
                            {bookmakerInfo.short}
                          </span>
                        </button>
                      )}
                      <span className={`${textSecondary} text-base`}>{odd.bookmaker}</span>
                      {shouldHighlight && <span className="text-blue-300">⭐</span>}
                      <span className={`${getLatencyColor(odd.latency_ms)} text-base font-bold`} title="Slower books give you more time to react">
                        {formatLatency(odd.latency_ms)} {getBettorEdge(odd.latency_ms)}
                      </span>
                    </div>
                    {/* Display based on selected market */}
                    {selectedMarket === 'totals' && (
                      <span className={`${shouldHighlight ? 'text-blue-200 font-bold text-base' : `${textSecondary} font-bold`}`}>
                        O/U <span className="font-extrabold text-lg">{odd.total}</span> (<span className="font-bold">{odd.over_price > 0 ? '+' : ''}{odd.over_price}/{odd.under_price > 0 ? '+' : ''}{odd.under_price}</span>)
                      </span>
                    )}
                    {selectedMarket === 'spread' && (
                      <div className={`${shouldHighlight ? 'text-blue-200' : textSecondary} text-base font-bold flex gap-3`}>
                        <span>
                          {state.home_team.name.split(' ').pop()}: <span className="font-extrabold text-base">{odd.home_spread > 0 ? '+' : ''}{odd.home_spread}</span> <span className="text-sm">({odd.home_spread_price > 0 ? '+' : ''}{odd.home_spread_price})</span>
                        </span>
                        <span>
                          {state.away_team.name.split(' ').pop()}: <span className="font-extrabold text-base">{odd.away_spread > 0 ? '+' : ''}{odd.away_spread}</span> <span className="text-sm">({odd.away_spread_price > 0 ? '+' : ''}{odd.away_spread_price})</span>
                        </span>
                      </div>
                    )}
                    {selectedMarket === 'moneyline' && (
                      <div className={`${shouldHighlight ? 'text-blue-200' : textSecondary} text-base font-bold flex gap-3`}>
                        <span>
                          {state.home_team.name.split(' ').pop()}: <span className="font-extrabold text-base">{odd.home_ml > 0 ? '+' : ''}{odd.home_ml}</span>
                        </span>
                        <span>
                          {state.away_team.name.split(' ').pop()}: <span className="font-extrabold text-base">{odd.away_ml > 0 ? '+' : ''}{odd.away_ml}</span>
                        </span>
                      </div>
                    )}
                  </div>
                );
              });
            })()}
          </div>
        </div>
      )}

      {/* Best Spreads and ML Section */}
      {odds.length > 0 && odds.some(o => o.home_spread !== null && o.home_spread !== undefined) && (
        <div className={`${dividerClass} mt-3 pt-3`}>
          <div className={`text-lg ${textSecondary} font-bold mb-2`}>Best Available Lines</div>
          <div className="space-y-2 text-base">
            {/* Best Spreads */}
            {(() => {
              const oddsWithSpread = odds.filter(o => o.home_spread !== null && o.home_spread !== undefined);
              if (oddsWithSpread.length === 0) return null;

              // Find best spreads for each team (more favorable number + best price)
              const bestHomeSpread = oddsWithSpread.reduce((best, curr) => {
                if (!best) return curr;
                // Home team wants lowest spread (less points to give)
                if (curr.home_spread! > best.home_spread!) return curr;
                if (curr.home_spread === best.home_spread && (curr.home_spread_price || 0) > (best.home_spread_price || 0)) return curr;
                return best;
              });

              const bestAwaySpread = oddsWithSpread.reduce((best, curr) => {
                if (!best) return curr;
                // Away team wants highest spread (more points to get)
                if (curr.away_spread! > best.away_spread!) return curr;
                if (curr.away_spread === best.away_spread && (curr.away_spread_price || 0) > (best.away_spread_price || 0)) return curr;
                return best;
              });

              return (
                <div>
                  <div className={`text-base ${textLabel} mb-1 font-semibold`}>Spreads</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <span className={`${textSecondary} font-semibold`}>{state.away_team.name.split(' ').slice(-1)[0]}: </span>
                      <span className="text-green-400 font-bold">
                        {bestAwaySpread.away_spread! > 0 ? '+' : ''}{bestAwaySpread.away_spread}
                        ({bestAwaySpread.away_spread_price! > 0 ? '+' : ''}{bestAwaySpread.away_spread_price})
                      </span>
                      <span className={`${textMuted} text-base ml-1`}>@{bestAwaySpread.bookmaker}</span>
                    </div>
                    <div>
                      <span className={`${textSecondary} font-semibold`}>{state.home_team.name.split(' ').slice(-1)[0]}: </span>
                      <span className="text-green-400 font-bold">
                        {bestHomeSpread.home_spread! > 0 ? '+' : ''}{bestHomeSpread.home_spread}
                        ({bestHomeSpread.home_spread_price! > 0 ? '+' : ''}{bestHomeSpread.home_spread_price})
                      </span>
                      <span className={`${textMuted} text-base ml-1`}>@{bestHomeSpread.bookmaker}</span>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Best Money Lines */}
            {(() => {
              const oddsWithML = odds.filter(o => o.home_ml !== null && o.home_ml !== undefined);
              if (oddsWithML.length === 0) return null;

              // Find best ML for each team (highest odds = best value)
              const bestHomeML = oddsWithML.reduce((best, curr) => {
                if (!best) return curr;
                if (curr.home_ml! > best.home_ml!) return curr;
                return best;
              });

              const bestAwayML = oddsWithML.reduce((best, curr) => {
                if (!best) return curr;
                if (curr.away_ml! > best.away_ml!) return curr;
                return best;
              });

              return (
                <div>
                  <div className={`text-base ${textLabel} mb-1 font-semibold`}>Money Lines</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <span className={`${textSecondary} font-semibold`}>{state.away_team.name.split(' ').slice(-1)[0]}: </span>
                      <span className="text-blue-400 font-bold">
                        {bestAwayML.away_ml! > 0 ? '+' : ''}{bestAwayML.away_ml}
                      </span>
                      <span className={`${textMuted} text-base ml-1`}>@{bestAwayML.bookmaker}</span>
                    </div>
                    <div>
                      <span className={`${textSecondary} font-semibold`}>{state.home_team.name.split(' ').slice(-1)[0]}: </span>
                      <span className="text-blue-400 font-bold">
                        {bestHomeML.home_ml! > 0 ? '+' : ''}{bestHomeML.home_ml}
                      </span>
                      <span className={`${textMuted} text-base ml-1`}>@{bestHomeML.bookmaker}</span>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Team Stats Section - Moved to bottom */}
      {(away_team_stats || home_team_stats) && (
        <div className={`${dividerClass} mt-3 pt-3`}>
          <div className="mb-3">
            <div className={`text-base ${textLabel} mb-2`}>NBA Season Stats</div>
            <div className="flex gap-2">
              <button
                onClick={() => setStatsView('stats')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'stats'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Stats
              </button>
              <button
                onClick={() => setStatsView('rankings')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'rankings'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Ranks
              </button>
              <button
                onClick={() => setStatsView('combined')}
                className={`flex-1 px-3 py-2 rounded-lg text-lg font-semibold transition-all ${
                  statsView === 'combined'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Both
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-base">
            {/* Away Team Stats */}
            <div className="space-y-1">
              <div className={`${textHeader} font-bold mb-2 text-center text-base`}>{state.away_team.name}</div>
              {away_team_stats && (
                <>
                  {/* RANKINGS VIEW */}
                  {statsView === 'rankings' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG Rank:</span>
                        <span className={`font-bold ${getRankColor(away_team_stats.pts_per_game_rank || 30)}`}>
                          #{away_team_stats.pts_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>OffRtg:</span>
                        <span className={`font-bold ${getRankColor(away_team_stats.off_rating_rank || 30)}`}>
                          #{away_team_stats.off_rating_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>DefRtg:</span>
                        <span className={`font-bold ${getRankColor(away_team_stats.def_rating_rank || 30)}`}>
                          #{away_team_stats.def_rating_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>NetRtg:</span>
                        <span className={`font-bold ${getRankColor(away_team_stats.net_rating_rank || 30)}`}>
                          #{away_team_stats.net_rating_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pace:</span>
                        <span className={`font-bold ${getRankColor(away_team_stats.pace_rank || 30)}`}>
                          #{away_team_stats.pace_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>FG%:</span>
                        <span className={`font-bold ${getRankColor(away_team_stats.fg_pct_rank || 30)}`}>
                          #{away_team_stats.fg_pct_rank || 'N/A'}
                        </span>
                      </div>
                    </>
                  )}

                  {/* COMBINED VIEW */}
                  {statsView === 'combined' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={`${
                          home_team_stats && away_team_stats.pts_per_game > home_team_stats.pts_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_team_stats.pts_per_game.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_team_stats.pts_per_game_rank || 30)}`}>
                            (#{away_team_stats.pts_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>OffRtg:</span>
                        <span className={`${
                          home_team_stats && away_team_stats.off_rating > home_team_stats.off_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_team_stats.off_rating.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_team_stats.off_rating_rank || 30)}`}>
                            (#{away_team_stats.off_rating_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>DefRtg:</span>
                        <span className={`${
                          home_team_stats && away_team_stats.def_rating < home_team_stats.def_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_team_stats.def_rating.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_team_stats.def_rating_rank || 30)}`}>
                            (#{away_team_stats.def_rating_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>NetRtg:</span>
                        <span className={`${
                          home_team_stats && away_team_stats.net_rating > home_team_stats.net_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_team_stats.net_rating.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_team_stats.net_rating_rank || 30)}`}>
                            (#{away_team_stats.net_rating_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pace:</span>
                        <span className={`${
                          home_team_stats && away_team_stats.pace > home_team_stats.pace
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {away_team_stats.pace.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(away_team_stats.pace_rank || 30)}`}>
                            (#{away_team_stats.pace_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>FG%:</span>
                        <span className={`${
                          home_team_stats && away_team_stats.fg_pct > home_team_stats.fg_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {(away_team_stats.fg_pct * 100).toFixed(1)}%
                          <span className={`text-sm ml-1 ${getRankColor(away_team_stats.fg_pct_rank || 30)}`}>
                            (#{away_team_stats.fg_pct_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                    </>
                  )}

                  {/* STATS VIEW */}
                  {statsView === 'stats' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Record:</span>
                        <span className={`font-semibold ${
                          home_team_stats && away_team_stats.win_pct > home_team_stats.win_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{away_team_stats.wins}-{away_team_stats.losses}</span>
                      </div>
                      {away_team_stats.last_5_record && (
                        <div className="flex items-center justify-between">
                          <span className={`${textLabel}`}>L5:</span>
                          <div className="flex items-center gap-1">
                            <span className={`${textValue}`}>{away_team_stats.last_5_record}</span>
                            {away_team_stats.form_trend === 'HOT' && (
                              <span className="px-1 py-0.5 bg-green-900 text-green-200 rounded text-sm">HOT</span>
                            )}
                            {away_team_stats.form_trend === 'COLD' && (
                              <span className="px-1 py-0.5 bg-red-900 text-red-200 rounded text-sm">COLD</span>
                            )}
                          </div>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={
                          home_team_stats && away_team_stats.pts_per_game > home_team_stats.pts_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_team_stats.pts_per_game.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>OffRtg:</span>
                        <span className={
                          home_team_stats && away_team_stats.off_rating > home_team_stats.off_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_team_stats.off_rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>DefRtg:</span>
                        <span className={
                          home_team_stats && away_team_stats.def_rating < home_team_stats.def_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_team_stats.def_rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pace:</span>
                        <span className={
                          home_team_stats && away_team_stats.pace > home_team_stats.pace
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{away_team_stats.pace.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>FG%:</span>
                        <span className={
                          home_team_stats && away_team_stats.fg_pct > home_team_stats.fg_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(away_team_stats.fg_pct * 100).toFixed(1)}%</span>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>

            {/* Home Team Stats */}
            <div className="space-y-1">
              <div className={`${textHeader} font-bold mb-2 text-center text-base`}>{state.home_team.name}</div>
              {home_team_stats && (
                <>
                  {/* RANKINGS VIEW */}
                  {statsView === 'rankings' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG Rank:</span>
                        <span className={`font-bold ${getRankColor(home_team_stats.pts_per_game_rank || 30)}`}>
                          #{home_team_stats.pts_per_game_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>OffRtg:</span>
                        <span className={`font-bold ${getRankColor(home_team_stats.off_rating_rank || 30)}`}>
                          #{home_team_stats.off_rating_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>DefRtg:</span>
                        <span className={`font-bold ${getRankColor(home_team_stats.def_rating_rank || 30)}`}>
                          #{home_team_stats.def_rating_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>NetRtg:</span>
                        <span className={`font-bold ${getRankColor(home_team_stats.net_rating_rank || 30)}`}>
                          #{home_team_stats.net_rating_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pace:</span>
                        <span className={`font-bold ${getRankColor(home_team_stats.pace_rank || 30)}`}>
                          #{home_team_stats.pace_rank || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>FG%:</span>
                        <span className={`font-bold ${getRankColor(home_team_stats.fg_pct_rank || 30)}`}>
                          #{home_team_stats.fg_pct_rank || 'N/A'}
                        </span>
                      </div>
                    </>
                  )}

                  {/* COMBINED VIEW */}
                  {statsView === 'combined' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={`${
                          away_team_stats && home_team_stats.pts_per_game > away_team_stats.pts_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_team_stats.pts_per_game.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_team_stats.pts_per_game_rank || 30)}`}>
                            (#{home_team_stats.pts_per_game_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>OffRtg:</span>
                        <span className={`${
                          away_team_stats && home_team_stats.off_rating > away_team_stats.off_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_team_stats.off_rating.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_team_stats.off_rating_rank || 30)}`}>
                            (#{home_team_stats.off_rating_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>DefRtg:</span>
                        <span className={`${
                          away_team_stats && home_team_stats.def_rating < away_team_stats.def_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_team_stats.def_rating.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_team_stats.def_rating_rank || 30)}`}>
                            (#{home_team_stats.def_rating_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>NetRtg:</span>
                        <span className={`${
                          away_team_stats && home_team_stats.net_rating > away_team_stats.net_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_team_stats.net_rating.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_team_stats.net_rating_rank || 30)}`}>
                            (#{home_team_stats.net_rating_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pace:</span>
                        <span className={`${
                          away_team_stats && home_team_stats.pace > away_team_stats.pace
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {home_team_stats.pace.toFixed(1)}
                          <span className={`text-sm ml-1 ${getRankColor(home_team_stats.pace_rank || 30)}`}>
                            (#{home_team_stats.pace_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>FG%:</span>
                        <span className={`${
                          away_team_stats && home_team_stats.fg_pct > away_team_stats.fg_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>
                          {(home_team_stats.fg_pct * 100).toFixed(1)}%
                          <span className={`text-sm ml-1 ${getRankColor(home_team_stats.fg_pct_rank || 30)}`}>
                            (#{home_team_stats.fg_pct_rank || 'N/A'})
                          </span>
                        </span>
                      </div>
                    </>
                  )}

                  {/* STATS VIEW */}
                  {statsView === 'stats' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Record:</span>
                        <span className={`font-semibold ${
                          away_team_stats && home_team_stats.win_pct > away_team_stats.win_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }`}>{home_team_stats.wins}-{home_team_stats.losses}</span>
                      </div>
                      {home_team_stats.last_5_record && (
                        <div className="flex items-center justify-between">
                          <span className={`${textLabel}`}>L5:</span>
                          <div className="flex items-center gap-1">
                            <span className={`${textValue}`}>{home_team_stats.last_5_record}</span>
                            {home_team_stats.form_trend === 'HOT' && (
                              <span className="px-1 py-0.5 bg-green-900 text-green-200 rounded text-sm">HOT</span>
                            )}
                            {home_team_stats.form_trend === 'COLD' && (
                              <span className="px-1 py-0.5 bg-red-900 text-red-200 rounded text-sm">COLD</span>
                            )}
                          </div>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>PPG:</span>
                        <span className={
                          away_team_stats && home_team_stats.pts_per_game > away_team_stats.pts_per_game
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_team_stats.pts_per_game.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>OffRtg:</span>
                        <span className={
                          away_team_stats && home_team_stats.off_rating > away_team_stats.off_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_team_stats.off_rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>DefRtg:</span>
                        <span className={
                          away_team_stats && home_team_stats.def_rating < away_team_stats.def_rating
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_team_stats.def_rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>Pace:</span>
                        <span className={
                          away_team_stats && home_team_stats.pace > away_team_stats.pace
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{home_team_stats.pace.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`${textLabel}`}>FG%:</span>
                        <span className={
                          away_team_stats && home_team_stats.fg_pct > away_team_stats.fg_pct
                            ? 'text-green-400'
                            : `${textValue}`
                        }>{(home_team_stats.fg_pct * 100).toFixed(1)}%</span>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* NFL Live Stats Section */}
      {sportBadge === 'NFL' && state.status === 'live' && (away_nfl_live_stats || home_nfl_live_stats) && (() => {
        // Helper function to parse numeric value from stat string (e.g., "150" from "150", "3-10" returns 3, "12:30" for possession)
        const parseStatValue = (stat: string | null | undefined, isPercentage = false): number | null => {
          if (!stat) return null;
          if (isPercentage) {
            // Handle efficiency like "3-10" (3/10)
            const parts = stat.split('-');
            if (parts.length === 2) {
              const made = parseInt(parts[0]);
              const total = parseInt(parts[1]);
              return total > 0 ? made / total : 0;
            }
          }
          // For possession time like "12:30", convert to minutes
          if (stat.includes(':')) {
            const [mins, secs] = stat.split(':').map(Number);
            return mins + secs / 60;
          }
          // Handle sacks like "2-15" (2 sacks for 15 yards)
          if (stat.includes('-')) {
            return parseFloat(stat.split('-')[0]);
          }
          return parseFloat(stat);
        };

        return (
        <div className={`${dividerClass} mt-3 pt-3`}>
          <div className={`text-base ${textLabel} mb-2 font-semibold`}>Live Game Stats</div>
          <div className="grid grid-cols-3 gap-2 text-base">
            {/* Stat Label Column */}
            <div className="space-y-1 text-center">
              <div className={`${textMuted} font-semibold`}>{state.away_team.name.split(' ').pop()}</div>
              {away_nfl_live_stats?.first_downs && <div className={`font-semibold ${
                home_nfl_live_stats?.first_downs && parseStatValue(away_nfl_live_stats.first_downs)! > parseStatValue(home_nfl_live_stats.first_downs)! ? 'text-green-400' : `${textSecondary}`
              }`}>{away_nfl_live_stats.first_downs}</div>}
              {away_nfl_live_stats?.first_downs_passing && <div className={
                home_nfl_live_stats?.first_downs_passing && parseStatValue(away_nfl_live_stats.first_downs_passing)! > parseStatValue(home_nfl_live_stats.first_downs_passing)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.first_downs_passing}</div>}
              {away_nfl_live_stats?.first_downs_rushing && <div className={
                home_nfl_live_stats?.first_downs_rushing && parseStatValue(away_nfl_live_stats.first_downs_rushing)! > parseStatValue(home_nfl_live_stats.first_downs_rushing)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.first_downs_rushing}</div>}
              {away_nfl_live_stats?.first_downs_penalty && <div className={`${textSecondary}`}>{away_nfl_live_stats.first_downs_penalty}</div>}
              {away_nfl_live_stats?.third_down_eff && <div className={
                home_nfl_live_stats?.third_down_eff && parseStatValue(away_nfl_live_stats.third_down_eff, true)! > parseStatValue(home_nfl_live_stats.third_down_eff, true)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.third_down_eff}</div>}
              {away_nfl_live_stats?.fourth_down_eff && <div className={
                home_nfl_live_stats?.fourth_down_eff && parseStatValue(away_nfl_live_stats.fourth_down_eff, true)! > parseStatValue(home_nfl_live_stats.fourth_down_eff, true)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.fourth_down_eff}</div>}
              {away_nfl_live_stats?.total_yards && <div className={`font-semibold ${
                home_nfl_live_stats?.total_yards && parseStatValue(away_nfl_live_stats.total_yards)! > parseStatValue(home_nfl_live_stats.total_yards)! ? 'text-green-400' : `${textSecondary}`
              }`}>{away_nfl_live_stats.total_yards}</div>}
              {away_nfl_live_stats?.yards_per_play && <div className={
                home_nfl_live_stats?.yards_per_play && parseStatValue(away_nfl_live_stats.yards_per_play)! > parseStatValue(home_nfl_live_stats.yards_per_play)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.yards_per_play}</div>}
              {away_nfl_live_stats?.comp_att && <div className={`${textSecondary}`}>{away_nfl_live_stats.comp_att}</div>}
              {away_nfl_live_stats?.passing_yards && <div className={
                home_nfl_live_stats?.passing_yards && parseStatValue(away_nfl_live_stats.passing_yards)! > parseStatValue(home_nfl_live_stats.passing_yards)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.passing_yards}</div>}
              {away_nfl_live_stats?.yards_per_pass && <div className={
                home_nfl_live_stats?.yards_per_pass && parseStatValue(away_nfl_live_stats.yards_per_pass)! > parseStatValue(home_nfl_live_stats.yards_per_pass)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.yards_per_pass}</div>}
              {away_nfl_live_stats?.interceptions_thrown && <div className={
                home_nfl_live_stats?.interceptions_thrown && parseStatValue(away_nfl_live_stats.interceptions_thrown)! < parseStatValue(home_nfl_live_stats.interceptions_thrown)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.interceptions_thrown}</div>}
              {away_nfl_live_stats?.sacks_yards_lost && <div className={
                home_nfl_live_stats?.sacks_yards_lost && parseStatValue(away_nfl_live_stats.sacks_yards_lost)! < parseStatValue(home_nfl_live_stats.sacks_yards_lost)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.sacks_yards_lost}</div>}
              {away_nfl_live_stats?.rushing_yards && <div className={
                home_nfl_live_stats?.rushing_yards && parseStatValue(away_nfl_live_stats.rushing_yards)! > parseStatValue(home_nfl_live_stats.rushing_yards)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.rushing_yards}</div>}
              {away_nfl_live_stats?.rushing_attempts && <div className={`${textSecondary}`}>{away_nfl_live_stats.rushing_attempts}</div>}
              {away_nfl_live_stats?.yards_per_rush && <div className={
                home_nfl_live_stats?.yards_per_rush && parseStatValue(away_nfl_live_stats.yards_per_rush)! > parseStatValue(home_nfl_live_stats.yards_per_rush)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.yards_per_rush}</div>}
              {away_nfl_live_stats?.red_zone && <div className={
                home_nfl_live_stats?.red_zone && parseStatValue(away_nfl_live_stats.red_zone, true)! > parseStatValue(home_nfl_live_stats.red_zone, true)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.red_zone}</div>}
              {away_nfl_live_stats?.penalties && <div className={
                home_nfl_live_stats?.penalties && parseStatValue(away_nfl_live_stats.penalties)! < parseStatValue(home_nfl_live_stats.penalties)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.penalties}</div>}
              {away_nfl_live_stats?.turnovers && <div className={
                home_nfl_live_stats?.turnovers && parseStatValue(away_nfl_live_stats.turnovers)! < parseStatValue(home_nfl_live_stats.turnovers)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.turnovers}</div>}
              {away_nfl_live_stats?.fumbles_lost && <div className={
                home_nfl_live_stats?.fumbles_lost && parseStatValue(away_nfl_live_stats.fumbles_lost)! < parseStatValue(home_nfl_live_stats.fumbles_lost)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.fumbles_lost}</div>}
              {away_nfl_live_stats?.possession && <div className={
                home_nfl_live_stats?.possession && parseStatValue(away_nfl_live_stats.possession)! > parseStatValue(home_nfl_live_stats.possession)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.possession}</div>}
              {away_nfl_live_stats?.total_plays && <div className={
                home_nfl_live_stats?.total_plays && parseStatValue(away_nfl_live_stats.total_plays)! > parseStatValue(home_nfl_live_stats.total_plays)! ? 'text-green-400' : `${textSecondary}`
              }>{away_nfl_live_stats.total_plays}</div>}
            </div>

            {/* Middle Column - Stat Names */}
            <div className="space-y-1 text-center">
              <div className={`${textLabel} font-semibold`}>Stat</div>
              {away_nfl_live_stats?.first_downs && <div className={`${textLabel} font-semibold`}>1st Downs</div>}
              {away_nfl_live_stats?.first_downs_passing && <div className={`${textLabel}`}>Passing 1st</div>}
              {away_nfl_live_stats?.first_downs_rushing && <div className={`${textLabel}`}>Rushing 1st</div>}
              {away_nfl_live_stats?.first_downs_penalty && <div className={`${textLabel}`}>1st from Pen</div>}
              {away_nfl_live_stats?.third_down_eff && <div className={`${textLabel}`}>3rd Down</div>}
              {away_nfl_live_stats?.fourth_down_eff && <div className={`${textLabel}`}>4th Down</div>}
              {away_nfl_live_stats?.total_yards && <div className={`${textLabel} font-semibold`}>Total Yards</div>}
              {away_nfl_live_stats?.yards_per_play && <div className={`${textLabel}`}>Yds/Play</div>}
              {away_nfl_live_stats?.comp_att && <div className={`${textLabel}`}>Comp/Att</div>}
              {away_nfl_live_stats?.passing_yards && <div className={`${textLabel}`}>Pass Yds</div>}
              {away_nfl_live_stats?.yards_per_pass && <div className={`${textLabel}`}>Yds/Pass</div>}
              {away_nfl_live_stats?.interceptions_thrown && <div className={`${textLabel}`}>INTs</div>}
              {away_nfl_live_stats?.sacks_yards_lost && <div className={`${textLabel}`}>Sacks-Yds</div>}
              {away_nfl_live_stats?.rushing_yards && <div className={`${textLabel}`}>Rush Yds</div>}
              {away_nfl_live_stats?.rushing_attempts && <div className={`${textLabel}`}>Rush Att</div>}
              {away_nfl_live_stats?.yards_per_rush && <div className={`${textLabel}`}>Yds/Rush</div>}
              {away_nfl_live_stats?.red_zone && <div className={`${textLabel}`}>Red Zone</div>}
              {away_nfl_live_stats?.penalties && <div className={`${textLabel}`}>Penalties</div>}
              {away_nfl_live_stats?.turnovers && <div className={`${textLabel}`}>Turnovers</div>}
              {away_nfl_live_stats?.fumbles_lost && <div className={`${textLabel}`}>Fumbles</div>}
              {away_nfl_live_stats?.possession && <div className={`${textLabel}`}>Possession</div>}
              {away_nfl_live_stats?.total_plays && <div className={`${textLabel}`}>Total Plays</div>}
            </div>

            {/* Home Team Column */}
            <div className="space-y-1 text-center">
              <div className={`${textMuted} font-semibold`}>{state.home_team.name.split(' ').pop()}</div>
              {home_nfl_live_stats?.first_downs && <div className={`font-semibold ${
                away_nfl_live_stats?.first_downs && parseStatValue(home_nfl_live_stats.first_downs)! > parseStatValue(away_nfl_live_stats.first_downs)! ? 'text-green-400' : `${textSecondary}`
              }`}>{home_nfl_live_stats.first_downs}</div>}
              {home_nfl_live_stats?.first_downs_passing && <div className={
                away_nfl_live_stats?.first_downs_passing && parseStatValue(home_nfl_live_stats.first_downs_passing)! > parseStatValue(away_nfl_live_stats.first_downs_passing)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.first_downs_passing}</div>}
              {home_nfl_live_stats?.first_downs_rushing && <div className={
                away_nfl_live_stats?.first_downs_rushing && parseStatValue(home_nfl_live_stats.first_downs_rushing)! > parseStatValue(away_nfl_live_stats.first_downs_rushing)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.first_downs_rushing}</div>}
              {home_nfl_live_stats?.first_downs_penalty && <div className={`${textSecondary}`}>{home_nfl_live_stats.first_downs_penalty}</div>}
              {home_nfl_live_stats?.third_down_eff && <div className={
                away_nfl_live_stats?.third_down_eff && parseStatValue(home_nfl_live_stats.third_down_eff, true)! > parseStatValue(away_nfl_live_stats.third_down_eff, true)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.third_down_eff}</div>}
              {home_nfl_live_stats?.fourth_down_eff && <div className={
                away_nfl_live_stats?.fourth_down_eff && parseStatValue(home_nfl_live_stats.fourth_down_eff, true)! > parseStatValue(away_nfl_live_stats.fourth_down_eff, true)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.fourth_down_eff}</div>}
              {home_nfl_live_stats?.total_yards && <div className={`font-semibold ${
                away_nfl_live_stats?.total_yards && parseStatValue(home_nfl_live_stats.total_yards)! > parseStatValue(away_nfl_live_stats.total_yards)! ? 'text-green-400' : `${textSecondary}`
              }`}>{home_nfl_live_stats.total_yards}</div>}
              {home_nfl_live_stats?.yards_per_play && <div className={
                away_nfl_live_stats?.yards_per_play && parseStatValue(home_nfl_live_stats.yards_per_play)! > parseStatValue(away_nfl_live_stats.yards_per_play)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.yards_per_play}</div>}
              {home_nfl_live_stats?.comp_att && <div className={`${textSecondary}`}>{home_nfl_live_stats.comp_att}</div>}
              {home_nfl_live_stats?.passing_yards && <div className={
                away_nfl_live_stats?.passing_yards && parseStatValue(home_nfl_live_stats.passing_yards)! > parseStatValue(away_nfl_live_stats.passing_yards)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.passing_yards}</div>}
              {home_nfl_live_stats?.yards_per_pass && <div className={
                away_nfl_live_stats?.yards_per_pass && parseStatValue(home_nfl_live_stats.yards_per_pass)! > parseStatValue(away_nfl_live_stats.yards_per_pass)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.yards_per_pass}</div>}
              {home_nfl_live_stats?.interceptions_thrown && <div className={
                away_nfl_live_stats?.interceptions_thrown && parseStatValue(home_nfl_live_stats.interceptions_thrown)! < parseStatValue(away_nfl_live_stats.interceptions_thrown)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.interceptions_thrown}</div>}
              {home_nfl_live_stats?.sacks_yards_lost && <div className={
                away_nfl_live_stats?.sacks_yards_lost && parseStatValue(home_nfl_live_stats.sacks_yards_lost)! < parseStatValue(away_nfl_live_stats.sacks_yards_lost)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.sacks_yards_lost}</div>}
              {home_nfl_live_stats?.rushing_yards && <div className={
                away_nfl_live_stats?.rushing_yards && parseStatValue(home_nfl_live_stats.rushing_yards)! > parseStatValue(away_nfl_live_stats.rushing_yards)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.rushing_yards}</div>}
              {home_nfl_live_stats?.rushing_attempts && <div className={`${textSecondary}`}>{home_nfl_live_stats.rushing_attempts}</div>}
              {home_nfl_live_stats?.yards_per_rush && <div className={
                away_nfl_live_stats?.yards_per_rush && parseStatValue(home_nfl_live_stats.yards_per_rush)! > parseStatValue(away_nfl_live_stats.yards_per_rush)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.yards_per_rush}</div>}
              {home_nfl_live_stats?.red_zone && <div className={
                away_nfl_live_stats?.red_zone && parseStatValue(home_nfl_live_stats.red_zone, true)! > parseStatValue(away_nfl_live_stats.red_zone, true)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.red_zone}</div>}
              {home_nfl_live_stats?.penalties && <div className={
                away_nfl_live_stats?.penalties && parseStatValue(home_nfl_live_stats.penalties)! < parseStatValue(away_nfl_live_stats.penalties)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.penalties}</div>}
              {home_nfl_live_stats?.turnovers && <div className={
                away_nfl_live_stats?.turnovers && parseStatValue(home_nfl_live_stats.turnovers)! < parseStatValue(away_nfl_live_stats.turnovers)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.turnovers}</div>}
              {home_nfl_live_stats?.fumbles_lost && <div className={
                away_nfl_live_stats?.fumbles_lost && parseStatValue(home_nfl_live_stats.fumbles_lost)! < parseStatValue(away_nfl_live_stats.fumbles_lost)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.fumbles_lost}</div>}
              {home_nfl_live_stats?.possession && <div className={
                away_nfl_live_stats?.possession && parseStatValue(home_nfl_live_stats.possession)! > parseStatValue(away_nfl_live_stats.possession)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.possession}</div>}
              {home_nfl_live_stats?.total_plays && <div className={
                away_nfl_live_stats?.total_plays && parseStatValue(home_nfl_live_stats.total_plays)! > parseStatValue(away_nfl_live_stats.total_plays)! ? 'text-green-400' : `${textSecondary}`
              }>{home_nfl_live_stats.total_plays}</div>}
            </div>
          </div>
        </div>
        )
      })()}
    </div>
  );
}
