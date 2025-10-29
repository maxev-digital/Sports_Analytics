export const Footer = () => {
  return (
    <footer className="bg-black text-slate-400 text-xs py-6 text-center border-t border-slate-800">
      <p className="mb-2">
        © 2025 <strong>Max EV Holdings, LLC</strong>. All rights reserved.
        Wyoming Limited Liability Company • Filing ID: <span className="text-yellow-500">2025-001800389</span>
      </p>
      <p className="max-w-4xl mx-auto leading-relaxed px-4">
        <strong>NOT FINANCIAL ADVICE.</strong> Max EV provides data, analytics, and alerts for informational and entertainment purposes only.
        Nothing on this site constitutes investment, financial, legal, or gambling advice.
        <strong> You are solely responsible for your betting decisions and any resulting losses.</strong>
        <br /><br />
        Use of this platform does not guarantee profits. Past performance is not indicative of future results.
        Gambling involves risk and may lead to addiction. If you or someone you know has a gambling problem,
        call 1-800-GAMBLER or visit <a href="https://www.ncpgambling.org" className="underline text-yellow-400 hover:text-yellow-300" target="_blank" rel="noopener noreferrer">ncpgambling.org</a>.
      </p>
      <p className="mt-4 text-xs">
        <a href="/terms" className="underline hover:text-yellow-400">Terms of Service</a> • {' '}
        <a href="/privacy" className="underline hover:text-yellow-400">Privacy Policy</a> • {' '}
        <a href="/disclaimer" className="underline hover:text-yellow-400">Full Disclaimer</a>
      </p>
    </footer>
  );
};
