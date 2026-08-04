import { BOOKMAKERS } from '../../data/bookmakers';

export function getBookmakerInfo(bookmaker: string): { logo: string; short: string; bg: string; text: string } {
  const key = bookmaker.toLowerCase().replace(/\s+/g, '').replace(/\./g, '');
  const data = BOOKMAKERS[key] || BOOKMAKERS[key.replace(/_/g, '')];
  if (data) {
    return { logo: data.logo ?? '', short: bookmaker.substring(0, 3).toUpperCase(), bg: 'bg-slate-800', text: 'text-slate-200' };
  }
  // Hardcoded fallbacks for common books
  const fallback: Record<string, { logo: string; short: string; bg: string; text: string }> = {
    DraftKings:  { logo: 'https://sportsbook-brands.draftkings.com/images/dk-sportsbook-logo.svg', short: 'DK',  bg: 'bg-green-900',  text: 'text-green-200'  },
    FanDuel:     { logo: 'https://www.fanduel.com/favicon.svg',                                   short: 'FD',  bg: 'bg-blue-900',   text: 'text-blue-200'   },
    BetMGM:      { logo: 'https://sports.betmgm.com/assets/img/logos/betmgm-logo.svg',            short: 'MGM', bg: 'bg-yellow-900', text: 'text-yellow-200' },
    Caesars:     { logo: '',                                                                        short: 'CZR', bg: 'bg-purple-900', text: 'text-purple-200' },
    BetRivers:   { logo: '',                                                                        short: 'BR',  bg: 'bg-cyan-900',   text: 'text-cyan-200'   },
    Fanatics:    { logo: '',                                                                        short: 'FAN', bg: 'bg-slate-800',  text: 'text-slate-200'  },
  };
  return fallback[bookmaker] ?? { logo: '', short: bookmaker.substring(0, 3).toUpperCase(), bg: 'bg-slate-800', text: 'text-slate-300' };
}

export function formatOdds(n: number | null | undefined): string {
  if (n == null) return '—';
  return n > 0 ? `+${n}` : `${n}`;
}
