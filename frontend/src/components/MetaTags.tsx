import { useLocation } from 'react-router-dom';

interface Props {
  title: string;
  description?: string;
  image?: string;
  noindex?: boolean;
}

const DEFAULT_DESC = 'AI-powered sports betting analytics with live odds, pregame handicapping, and proven edge signals across NFL, CFB, MLB, NBA, and NHL.';
const SITE_URL = 'https://max-ev-sports.com';
const DEFAULT_IMAGE = '/og-image.png';

export function MetaTags({ title, description = DEFAULT_DESC, image = DEFAULT_IMAGE, noindex = false }: Props) {
  const { pathname } = useLocation();
  const canonical = `${SITE_URL}${pathname}`;
  const fullTitle = title.includes('Max EV') ? title : `${title} — Max EV Sports`;

  return (
    <>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image.startsWith('http') ? image : `${SITE_URL}${image}`} />
      <meta property="og:url" content={canonical} />
      <meta property="og:type" content="website" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      {noindex && <meta name="robots" content="noindex, nofollow" />}
    </>
  );
}
