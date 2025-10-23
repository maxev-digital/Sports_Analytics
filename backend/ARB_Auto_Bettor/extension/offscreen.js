/**
 * Offscreen Document for Audio (Beeps + Text-to-Speech)
 * This runs in a hidden document context where Web Audio API and speechSynthesis are available
 */

console.log('[OFFSCREEN] Audio document loaded');

// Audio context for beeps
let audioContext = null;

function initAudio() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    console.log('[OFFSCREEN] AudioContext initialized');
  }
}

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'speak') {
    speak(message.text, message.rate, message.pitch, message.volume);
    sendResponse({ success: true });
    return true;
  }

  if (message.type === 'play_beep') {
    playBeep(message.frequency, message.duration, message.type, message.volume);
    sendResponse({ success: true });
    return true;
  }

  if (message.type === 'play_sequence') {
    playSequence(message.notes, message.volume).then(() => {
      sendResponse({ success: true });
    });
    return true; // Keep channel open for async
  }
});

// Play a beep sound
function playBeep(frequency = 800, duration = 0.2, type = 'sine', volume = 0.5) {
  initAudio();

  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);

  oscillator.frequency.value = frequency;
  oscillator.type = type;

  // Volume envelope (fade in/out)
  gainNode.gain.setValueAtTime(0, audioContext.currentTime);
  gainNode.gain.linearRampToValueAtTime(volume, audioContext.currentTime + 0.01);
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);

  oscillator.start(audioContext.currentTime);
  oscillator.stop(audioContext.currentTime + duration);

  console.log(`[OFFSCREEN] 🔊 Beep: ${frequency}Hz ${duration}s`);
}

// Play sequence of beeps
async function playSequence(notes, volume) {
  for (const note of notes) {
    playBeep(note.f, note.d, note.t || 'sine', volume);
    await sleep((note.d + (note.g || 0)) * 1000);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Text-to-Speech
function speak(text, rate = 1.0, pitch = 1.0, volume = 0.5) {
  if (!window.speechSynthesis) {
    console.error('[OFFSCREEN] Speech synthesis not available');
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = rate;
  utterance.pitch = pitch;
  utterance.volume = volume;

  // Wait for voices to load
  const voices = window.speechSynthesis.getVoices();
  if (voices.length === 0) {
    // Voices not loaded yet, wait for them
    window.speechSynthesis.onvoiceschanged = () => {
      setVoiceAndSpeak(utterance);
    };
  } else {
    setVoiceAndSpeak(utterance);
  }
}

function setVoiceAndSpeak(utterance) {
  const voices = window.speechSynthesis.getVoices();

  // Prefer English voices
  const preferredVoice = voices.find(v =>
    v.lang.startsWith('en-US') && (v.name.includes('Google') || v.name.includes('Microsoft'))
  ) || voices.find(v => v.lang.startsWith('en'));

  if (preferredVoice) {
    utterance.voice = preferredVoice;
    console.log('[OFFSCREEN] Using voice:', preferredVoice.name);
  }

  console.log('[OFFSCREEN] 🗣️ Speaking:', utterance.text);
  window.speechSynthesis.speak(utterance);
}
