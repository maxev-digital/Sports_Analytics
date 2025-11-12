import React from 'react';
import { ROADMAP } from '../../data/futureFeatures';

export const TimelineSection: React.FC = () => {
  return (
    <section className="py-20 px-4 bg-gradient-to-br from-slate-900 via-blue-900/20 to-slate-900">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Development Roadmap
          </h2>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto">
            Track our progress from foundation to production-grade ML system.
            Each quarter brings powerful new features and improved performance.
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical Line */}
          <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-green-500 via-blue-500 via-purple-500 to-orange-500 transform md:-translate-x-1/2"></div>

          {/* Timeline Items */}
          <div className="space-y-12">
            {ROADMAP.map((release, idx) => {
              const isCompleted = release.status === 'completed';
              const isInProgress = release.status === 'in_progress';
              const isLeft = idx % 2 === 0;

              const statusColors = {
                completed: 'border-green-500 bg-green-950/30',
                in_progress: 'border-blue-500 bg-blue-950/30',
                planned: 'border-slate-600 bg-slate-800/30'
              };

              const statusBadges = {
                completed: 'bg-green-500 text-white',
                in_progress: 'bg-blue-500 text-white',
                planned: 'bg-slate-600 text-slate-300'
              };

              const statusLabels = {
                completed: '✓ COMPLETE',
                in_progress: '⚡ IN PROGRESS',
                planned: '📋 PLANNED'
              };

              return (
                <div
                  key={idx}
                  className={`relative ${
                    isLeft ? 'md:pr-1/2 md:text-right' : 'md:pl-1/2 md:ml-auto md:text-left'
                  }`}
                >
                  {/* Timeline Dot */}
                  <div className={`absolute left-8 md:left-1/2 transform md:-translate-x-1/2 ${
                    isCompleted ? 'bg-green-500' : isInProgress ? 'bg-blue-500' : 'bg-slate-600'
                  } w-6 h-6 rounded-full border-4 border-slate-900 z-10`}>
                    {isCompleted && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                    {isInProgress && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                      </div>
                    )}
                  </div>

                  {/* Content Card */}
                  <div className={`ml-20 md:ml-0 md:mr-12 ${!isLeft && 'md:ml-12 md:mr-0'} ${statusColors[release.status]} rounded-xl p-6 border-2 backdrop-blur-sm`}>
                    {/* Header */}
                    <div className={`flex items-start justify-between mb-4 ${isLeft ? 'md:flex-row-reverse' : ''}`}>
                      <div className={isLeft ? 'md:text-right' : ''}>
                        <div className="text-2xl font-bold text-white mb-1">
                          {release.quarter}
                        </div>
                        <div className="text-lg text-slate-300 font-semibold">
                          {release.phase}
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${statusBadges[release.status]} whitespace-nowrap`}>
                        {statusLabels[release.status]}
                      </span>
                    </div>

                    {/* Progress Bar (for in-progress) */}
                    {isInProgress && release.completion_percent !== undefined && (
                      <div className="mb-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-xs text-slate-400">Progress</span>
                          <span className="text-xs text-blue-400 font-semibold">
                            {release.completion_percent}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${release.completion_percent}%` }}
                          ></div>
                        </div>
                      </div>
                    )}

                    {/* Features List */}
                    <div className="mb-4">
                      <div className="text-sm text-slate-400 mb-2">Key Features:</div>
                      <ul className={`space-y-2 ${isLeft ? 'md:text-right' : ''}`}>
                        {release.features.map((feature, featureIdx) => (
                          <li
                            key={featureIdx}
                            className={`text-sm text-slate-300 flex items-start gap-2 ${
                              isLeft ? 'md:flex-row-reverse md:justify-end' : ''
                            }`}
                          >
                            <span className={isCompleted ? 'text-green-400' : 'text-blue-400'}>
                              {isCompleted ? '✓' : '•'}
                            </span>
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Expected Impact */}
                    <div className={`bg-slate-900/50 rounded-lg p-3 ${isLeft ? 'md:text-right' : ''}`}>
                      <div className="text-xs text-slate-400 mb-1">Expected Impact:</div>
                      <div className="text-sm font-semibold text-white">
                        {release.expected_impact}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-green-900/30 to-slate-900 rounded-xl p-6 border border-green-500/30 text-center">
            <div className="text-4xl mb-2">✓</div>
            <div className="text-3xl font-bold text-green-400 mb-2">
              {ROADMAP.filter(r => r.status === 'completed').length}
            </div>
            <div className="text-sm text-slate-400">Phases Completed</div>
          </div>

          <div className="bg-gradient-to-br from-blue-900/30 to-slate-900 rounded-xl p-6 border border-blue-500/30 text-center">
            <div className="text-4xl mb-2">⚡</div>
            <div className="text-3xl font-bold text-blue-400 mb-2">
              {ROADMAP.filter(r => r.status === 'in_progress').length}
            </div>
            <div className="text-sm text-slate-400">Currently Building</div>
          </div>

          <div className="bg-gradient-to-br from-purple-900/30 to-slate-900 rounded-xl p-6 border border-purple-500/30 text-center">
            <div className="text-4xl mb-2">📋</div>
            <div className="text-3xl font-bold text-purple-400 mb-2">
              {ROADMAP.filter(r => r.status === 'planned').length}
            </div>
            <div className="text-sm text-slate-400">Phases Planned</div>
          </div>
        </div>

        {/* Bottom Note */}
        <div className="mt-12 text-center">
          <p className="text-slate-400 text-sm max-w-2xl mx-auto">
            Timeline is subject to change based on testing results and user feedback.
            We prioritize quality and accuracy over speed.
          </p>
        </div>
      </div>
    </section>
  );
};
