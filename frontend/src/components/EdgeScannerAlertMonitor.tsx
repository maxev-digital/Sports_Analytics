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
import { logger } from '../utils/logger';

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

  const shouldMonitor = enabled && username;

  // Use the Edge Scanner alerts hook
  const { seenCount, isEnabled } = useEdgeScannerAlerts({
    enabled: !!shouldMonitor,
    minEdge,
    minConfidence,
    pollInterval,
    sports
  });

  // Track monitoring status
  useEffect(() => {
    setIsMonitoring(isEnabled && !!shouldMonitor);
  }, [isEnabled, shouldMonitor]);

  // Log monitoring status for debugging
  useEffect(() => {
    if (isMonitoring) {
      logger.info('🤖 Edge Scanner Alert Monitor: ACTIVE');
      logger.info(`   - Min Edge: ${minEdge}+`);
      logger.info(`   - Min Confidence: ${(minConfidence * 100).toFixed(0)}%+`);
      logger.info(`   - Poll Interval: ${pollInterval / 1000}s`);
      logger.info(`   - Sports Filter: ${sports.length > 0 ? sports.join(', ') : 'ALL'}`);
      logger.info(`   - Alerts Seen: ${seenCount}`);
    } else {
      logger.info('🤖 Edge Scanner Alert Monitor: INACTIVE');
      if (!username) logger.info('   - Reason: Not logged in');
      if (subscriptionTier !== 'elite') logger.info('   - Reason: No Elite subscription');
      if (!enabled) logger.info('   - Reason: Manually disabled');
    }
  }, [isMonitoring, minEdge, minConfidence, pollInterval, sports, seenCount, username, subscriptionTier, enabled]);

  // This component renders nothing
  return null;
}

export default EdgeScannerAlertMonitor;
