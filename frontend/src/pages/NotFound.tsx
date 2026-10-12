import { useNavigate } from 'react-router-dom';
import { MetaTags } from '../components/MetaTags';

export function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <MetaTags title="Page Not Found" description="The page you're looking for doesn't exist." noindex />
      <div className="text-center max-w-md">
        <div className="text-8xl font-black text-slate-700 mb-4">404</div>
        <h1 className="text-2xl font-bold text-slate-100 mb-2">Page Not Found</h1>
        <p className="text-slate-400 mb-8">The page you're looking for doesn't exist or has been moved.</p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => navigate('/todays-plays')}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-semibold text-sm hover:bg-blue-500 transition-colors"
          >
            Today's Plays
          </button>
          <button
            onClick={() => navigate('/live-games')}
            className="px-5 py-2.5 bg-slate-800 text-slate-300 rounded-lg font-semibold text-sm hover:bg-slate-700 border border-slate-700 transition-colors"
          >
            Matchups
          </button>
        </div>
      </div>
    </div>
  );
}
