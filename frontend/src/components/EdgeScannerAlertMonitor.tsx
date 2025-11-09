/**
 * Edge Scanner Alert Monitor Component
 *
 * Runs in the background to monitor for high-value live betting opportunities
 * from the ML Edge Scanner and triggers toast notifications.
 *
 * This component renders nothing visually - it just manages the alert monitoring.
 */

import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useEdgeScannerAlerts } from '../hooks/useEdgeScannerAlerts';

interface EdgeScannerAlertMonitorProps {
  enabled?: boolean;           // Enable/disable monitoring
  minEdge?: number;           // Minimum edge threshold
  minConfidence?: number;     // Minimum confidence threshold
  pollInterval?: number;      // How often to check (ms)
  sports?: string[];          // Filter by sports
}

export function EdgeScannerAlertMonitor({
  enabled = true,
  minEdge = 3.5,
  minConfidence = 0.70,
  pollInterval = 20000,
  sports = []
}: EdgeScannerAlertMonitorProps) {
  const { username, subscriptionTier } = useAuth();
  const [isMonitoring, setIsMonitoring] = useState(false);

  // Only enable monitoring if user is logged in and has active subscription
  const shouldMonitor = enabled && username && subscriptionTier === 'elite';

  // Use the Edge Scanner alerts hook
  const { seenCount, isEnabled } = useEdgeScannerAlerts({
    enabled: shouldMonitor,
    minEdge,
    minConfidence,
    pollInterval,
    sports
  });

  // Track monitoring status
  useEffect(() => {
    setIsMonitoring(isEnabled && shouldMonitor);
  }, [isEnabled, shouldMonitor]);

  // Log monitoring status for debugging
  useEffect(() => {
    if (isMonitoring) {
      console.log('🤖 Edge Scanner Alert Monitor: ACTIVE');
      console.log(`   - Min Edge: ${minEdge}+`);
      console.log(`   - Min Confidence: ${(minConfidence * 100).toFixed(0)}%+`);
      console.log(`   - Poll Interval: ${pollInterval / 1000}s`);
      console.log(`   - Sports Filter: ${sports.length > 0 ? sports.join(', ') : 'ALL'}`);
      console.log(`   - Alerts Seen: ${seenCount}`);
    } else {
      console.log('🤖 Edge Scanner Alert Monitor: INACTIVE');
      if (!username) console.log('   - Reason: Not logged in');
      if (subscriptionTier !== 'elite') console.log('   - Reason: No Elite subscription');
      if (!enabled) console.log('   - Reason: Manually disabled');
    }
  }, [isMonitoring, minEdge, minConfidence, pollInterval, sports, seenCount, username, subscriptionTier, enabled]);

  // This component renders nothing
  return null;
}

export default EdgeScannerAlertMonitor;
