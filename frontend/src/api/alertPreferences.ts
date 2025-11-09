/**
 * API service for managing system alert preferences
 */
import { getApiUrl } from '../config';

export interface AlertPreference {
  alerts_enabled: boolean;
  notification_method: string;
  min_strength_threshold: number;
  enabled_at: string;
  updated_at: string;
}

export interface AlertPreferencesResponse {
  user_id: string;
  preferences: { [systemId: number]: AlertPreference };
  enabled_systems: number[];
}

export interface ToggleResponse {
  success: boolean;
  message: string;
  system_id: number;
  alerts_enabled: boolean;
}

/**
 * Get all alert preferences for a user
 */
export async function getAlertPreferences(userId: string): Promise<AlertPreferencesResponse> {
  const response = await fetch(getApiUrl(`alert-preferences/${userId}`));

  if (!response.ok) {
    throw new Error(`Failed to fetch alert preferences: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get alert preferences for a specific system
 */
export async function getSystemPreference(userId: string, systemId: number): Promise<AlertPreference | null> {
  const response = await fetch(getApiUrl(`alert-preferences/${userId}/system/${systemId}`));

  if (!response.ok) {
    throw new Error(`Failed to fetch system preference: ${response.statusText}`);
  }

  const data = await response.json();
  return data.preferences;
}

/**
 * Enable alerts for a system
 */
export async function enableSystemAlerts(
  userId: string,
  systemId: number,
  notificationMethod: string = 'in_app',
  minStrength: number = 50.0
): Promise<ToggleResponse> {
  const response = await fetch(getApiUrl(`alert-preferences/${userId}/enable`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      system_id: systemId,
      notification_method: notificationMethod,
      min_strength: minStrength
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to enable alerts: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Disable alerts for a system
 */
export async function disableSystemAlerts(userId: string, systemId: number): Promise<ToggleResponse> {
  const response = await fetch(getApiUrl(`alert-preferences/${userId}/disable`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      system_id: systemId
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to disable alerts: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Toggle alerts for a system
 */
export async function toggleSystemAlerts(userId: string, systemId: number): Promise<ToggleResponse> {
  const response = await fetch(getApiUrl(`alert-preferences/${userId}/toggle`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      system_id: systemId
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to toggle alerts: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update notification method for a system
 */
export async function updateNotificationMethod(
  userId: string,
  systemId: number,
  notificationMethod: string
): Promise<{ success: boolean; message: string }> {
  const response = await fetch(getApiUrl(`alert-preferences/${userId}/update-notification-method`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      system_id: systemId,
      notification_method: notificationMethod
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to update notification method: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update minimum strength threshold
 */
export async function updateMinStrength(
  userId: string,
  systemId: number,
  minStrength: number
): Promise<{ success: boolean; message: string }> {
  const response = await fetch(getApiUrl(`alert-preferences/${userId}/update-min-strength`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      system_id: systemId,
      min_strength: minStrength
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to update min strength: ${response.statusText}`);
  }

  return response.json();
}
