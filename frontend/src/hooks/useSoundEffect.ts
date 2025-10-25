/**
 * Custom hook for playing sound effects throughout the app
 * Usage: const playSound = useSoundEffect('alert-bell.mp3', 0.3);
 *        playSound();
 */

import { useRef, useCallback } from 'react';

export function useSoundEffect(soundFile: string, volume: number = 0.3) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const play = useCallback(() => {
    try {
      if (!audioRef.current) {
        audioRef.current = new Audio(`/${soundFile}`);
        audioRef.current.volume = volume;
      }
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(err => {
        // Silently fail if audio can't play (e.g., user hasn't interacted with page yet)
        console.log('Sound play failed:', err);
      });
    } catch (error) {
      console.log('Sound error:', error);
    }
  }, [soundFile, volume]);

  return play;
}
