/**
 * Sound Alert System
 * Generates alert sounds using Web Audio API
 * No audio files needed - all sounds are synthesized!
 */

class SoundAlerts {
  constructor() {
    this.audioContext = null;
    this.enabled = true;
    this.volume = 0.5; // 0.0 to 1.0
  }

  /**
   * Initialize audio context (must be called after user interaction)
   */
  init() {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
  }

  /**
   * Play a beep sound
   * @param {number} frequency - Frequency in Hz
   * @param {number} duration - Duration in seconds
   * @param {string} type - Oscillator type: 'sine', 'square', 'triangle', 'sawtooth'
   */
  playBeep(frequency = 800, duration = 0.2, type = 'sine') {
    if (!this.enabled || !this.audioContext) return;

    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = type;

    // Volume envelope (fade in/out)
    gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(this.volume, this.audioContext.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);

    oscillator.start(this.audioContext.currentTime);
    oscillator.stop(this.audioContext.currentTime + duration);
  }

  /**
   * Play sequence of beeps
   * @param {Array} notes - Array of {frequency, duration} objects
   */
  async playSequence(notes) {
    if (!this.enabled || !this.audioContext) return;

    for (const note of notes) {
      this.playBeep(note.frequency, note.duration, note.type || 'sine');
      await this.sleep((note.duration + (note.gap || 0)) * 1000);
    }
  }

  /**
   * HIGH PRIORITY Alert - Urgent, attention-grabbing sound
   * 5%+ profit opportunities
   */
  async playHighPriority() {
    console.log('[SOUND] Playing HIGH priority alert');
    await this.playSequence([
      { frequency: 1200, duration: 0.15, type: 'square' },
      { frequency: 1400, duration: 0.15, type: 'square', gap: 0.05 },
      { frequency: 1200, duration: 0.15, type: 'square', gap: 0.05 },
      { frequency: 1400, duration: 0.15, type: 'square' }
    ]);
  }

  /**
   * MEDIUM PRIORITY Alert - Clear, noticeable sound
   * 3-5% profit opportunities
   */
  async playMediumPriority() {
    console.log('[SOUND] Playing MEDIUM priority alert');
    await this.playSequence([
      { frequency: 900, duration: 0.2, type: 'sine' },
      { frequency: 1100, duration: 0.2, type: 'sine', gap: 0.1 }
    ]);
  }

  /**
   * LOW PRIORITY Alert - Subtle notification
   * 2-3% profit opportunities
   */
  playLowPriority() {
    console.log('[SOUND] Playing LOW priority alert');
    this.playBeep(700, 0.15, 'sine');
  }

  /**
   * SUCCESS Sound - Confirmation sound
   */
  async playSuccess() {
    console.log('[SOUND] Playing success sound');
    await this.playSequence([
      { frequency: 600, duration: 0.1, type: 'sine' },
      { frequency: 800, duration: 0.15, type: 'sine', gap: 0.05 }
    ]);
  }

  /**
   * ERROR Sound - Warning/error sound
   */
  playError() {
    console.log('[SOUND] Playing error sound');
    this.playBeep(300, 0.3, 'sawtooth');
  }

  /**
   * NEW OPPORTUNITY Sound - Generic new opportunity
   */
  async playNewOpportunity(profitPercentage) {
    if (profitPercentage >= 5.0) {
      await this.playHighPriority();
    } else if (profitPercentage >= 3.0) {
      await this.playMediumPriority();
    } else {
      this.playLowPriority();
    }
  }

  /**
   * Enable/disable sounds
   */
  setEnabled(enabled) {
    this.enabled = enabled;
    console.log(`[SOUND] Alerts ${enabled ? 'enabled' : 'disabled'}`);
  }

  /**
   * Set volume (0.0 to 1.0)
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    console.log(`[SOUND] Volume set to ${(this.volume * 100).toFixed(0)}%`);
  }

  /**
   * Helper to sleep/delay
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Test all sounds
   */
  async testSounds() {
    console.log('[SOUND] Testing all alert sounds...');

    console.log('Testing HIGH priority...');
    await this.playHighPriority();
    await this.sleep(500);

    console.log('Testing MEDIUM priority...');
    await this.playMediumPriority();
    await this.sleep(500);

    console.log('Testing LOW priority...');
    this.playLowPriority();
    await this.sleep(500);

    console.log('[SOUND] Test complete!');
  }
}

// Create global instance
const soundAlerts = new SoundAlerts();

// Auto-initialize on first interaction
if (typeof window !== 'undefined') {
  window.addEventListener('click', () => soundAlerts.init(), { once: true });
}
