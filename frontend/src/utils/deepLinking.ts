/**
 * Mobile Deep Linking Utility
 * Handles smart deep linking for sportsbook apps
 *
 * Strategy:
 * 1. Universal Links (modern standard) - uses HTTPS URLs that automatically open apps
 * 2. Falls back to mobile web if app not installed
 * 3. Works on both iOS and Android
 */

/**
 * Detect if user is on mobile device
 */
export const isMobile = (): boolean => {
  if (typeof window === 'undefined') return false;

  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera;

  // Check for iOS
  const isIOS = /iPad|iPhone|iPod/.test(userAgent) && !(window as any).MSStream;

  // Check for Android
  const isAndroid = /android/i.test(userAgent);

  // Check for mobile-specific patterns
  const isMobileUA = /mobile/i.test(userAgent);

  return isIOS || isAndroid || isMobileUA;
};

/**
 * Detect specific mobile OS
 */
export const getMobileOS = (): 'iOS' | 'Android' | 'Other' | null => {
  if (typeof window === 'undefined') return null;

  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera;

  if (/iPad|iPhone|iPod/.test(userAgent) && !(window as any).MSStream) {
    return 'iOS';
  }

  if (/android/i.test(userAgent)) {
    return 'Android';
  }

  if (isMobile()) {
    return 'Other';
  }

  return null;
};

/**
 * Open sportsbook with smart deep linking
 *
 * On Mobile:
 * - Uses Universal Links (HTTPS URLs) which automatically open the app if installed
 * - Falls back to mobile website if app not installed
 *
 * On Desktop:
 * - Opens desktop website in new tab
 *
 * @param url - The sportsbook URL (should be Universal Link compatible)
 * @param bookmakerName - Name of the bookmaker for analytics/logging
 */
export const openSportsbook = (url: string, bookmakerName: string): void => {
  const mobile = isMobile();
  const mobileOS = getMobileOS();

  console.log(`Opening ${bookmakerName} - Mobile: ${mobile}, OS: ${mobileOS}`);

  if (mobile) {
    // Mobile: Use Universal Links approach
    // The URL itself will trigger app if installed, or mobile web if not
    // We use window.location instead of window.open for better app triggering
    window.location.href = url;
  } else {
    // Desktop: Open in new tab
    window.open(url, '_blank', 'noopener,noreferrer');
  }
};

/**
 * Get mobile-optimized URL for a sportsbook
 * Some sportsbooks have different mobile vs desktop URLs
 */
export const getMobileUrl = (desktopUrl: string, bookmakerKey: string): string => {
  // Most modern sportsbooks use responsive URLs that work on mobile and desktop
  // Universal Links use the same URL

  // Special cases for mobile-specific URLs
  const mobileOverrides: Record<string, string> = {
    // Add mobile-specific URLs here if needed
    // Example: 'draftkings': 'https://sportsbook.draftkings.com/...'
  };

  return mobileOverrides[bookmakerKey] || desktopUrl;
};

/**
 * Track deep link analytics (optional)
 */
export const trackDeepLink = (bookmakerName: string, opened: boolean): void => {
  // Add analytics tracking here if needed
  console.log(`Deep link - ${bookmakerName}: ${opened ? 'Opened' : 'Failed'}`);
};

export default {
  isMobile,
  getMobileOS,
  openSportsbook,
  getMobileUrl,
  trackDeepLink,
};
