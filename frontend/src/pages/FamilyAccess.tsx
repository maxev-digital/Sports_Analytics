import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getApiUrl } from '../config';

export function FamilyAccess() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('Setting up your access...');

  useEffect(() => {
    const code = searchParams.get('code') || 'FAMILY2026';

    fetch(getApiUrl(`auth/family?code=${code}`))
      .then(r => r.json())
      .then(data => {
        if (data.success && data.token) {
          localStorage.setItem('auth_token', data.token);
          localStorage.setItem('auth_username', data.username);
          localStorage.setItem('subscription_tier', 'will_the_thrill');
          localStorage.setItem('mes_access_granted', 'true');
          setStatus('You\'re in! Redirecting...');
          setTimeout(() => { window.location.href = '/#/live-games'; window.location.reload(); }, 1000);
        } else {
          setStatus('Invalid access link.');
        }
      })
      .catch(() => setStatus('Something went wrong. Try again.'));
  }, [searchParams]);

  return (
    <div style={{ minHeight: '100vh', background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', color: '#fff' }}>
        <div style={{
          width: 40, height: 40, borderRadius: '50%',
          border: '3px solid rgba(59,130,246,0.3)', borderTopColor: '#3B82F6',
          animation: 'spin 0.8s linear infinite', margin: '0 auto 20px',
        }} />
        <div style={{ fontSize: 18, fontWeight: 700 }}>{status}</div>
        <div style={{ fontSize: 13, color: '#666', marginTop: 8 }}>Max EV Sports — Full Access</div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </div>
  );
}

export default FamilyAccess;
