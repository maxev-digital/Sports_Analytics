import React from 'react';

interface SystemStatusBadgeProps {
  status: 'live' | 'active' | 'proven' | 'pending';
}

export const SystemStatusBadge: React.FC<SystemStatusBadgeProps> = ({ status }) => {
  const configs = {
    live: {
      bg: 'bg-green-600',
      border: 'border-green-400',
      text: 'text-white',
      icon: '✅',
      label: 'LIVE',
      description: 'Fully Operational'
    },
    proven: {
      bg: 'bg-yellow-600',
      border: 'border-yellow-400',
      text: 'text-white',
      icon: '⭐',
      label: 'PROVEN',
      description: 'Verified Performance'
    },
    active: {
      bg: 'bg-blue-600',
      border: 'border-blue-400',
      text: 'text-white',
      icon: '✅',
      label: 'ACTIVE',
      description: 'Backtested'
    },
    pending: {
      bg: 'bg-gray-600',
      border: 'border-gray-400',
      text: 'text-gray-300',
      icon: '⚠️',
      label: 'PENDING',
      description: 'Coming Soon'
    }
  };

  const config = configs[status];

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border-2 ${config.bg} ${config.border} ${config.text} font-bold text-xs`}
      title={config.description}
    >
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </div>
  );
};
