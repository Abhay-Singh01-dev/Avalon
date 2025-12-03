import { useState, useEffect, useRef, useCallback } from "react";

interface VoiceRecorderProps {
  onFinal?: (text: string) => void;
  onInterim?: (text: string) => void;
  onStart?: () => void;
  onStop?: () => void;
  onError?: (error: string) => void;
  autoStopOnSilence?: boolean;
  silenceThreshold?: number;
  silenceDuration?: number;
}

interface VoiceRecorderReturn {
  start: () => void;
  stop: () => void;
  isListening: boolean;
  interimTranscript: string;
  finalTranscript: string;
  volumeLevel: number;
  error: string | null;
  isSupported: boolean;
}

/**
 * Premium ChatGPT-style voice recorder with waveform visualization,
 * auto-stop on silence, echo suppression, and smooth animations.
 */
export const useVoiceRecorder = ({
  onFinal,
  onInterim,
  onStart,
  onStop,
  onError,
  autoStopOnSilence = true,
  silenceThreshold = 0.01,
  silenceDuration = 1000,
}: VoiceRecorderProps = {}): VoiceRecorderReturn => {
  // State
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [finalTranscript, setFinalTranscript] = useState("");
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);

  // Refs for Web Speech API
  const recognitionRef = useRef<any>(null);
  const lastFinalTranscriptRef = useRef<string>("");
  const isListeningRef = useRef<boolean>(false);
  const shouldStopRef = useRef<boolean>(false);

  // Refs for Web Audio API (volume detection & waveform)
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneStreamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Silence detection
  const silenceTimerRef = useRef<number | null>(null);
  const lastSoundTimeRef = useRef<number>(Date.now());

  /**
   * Initialize Speech Recognition API
   */
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("[VoiceRecorder] Speech Recognition API not supported");
      setIsSupported(false);
      setError("Speech recognition not supported in this browser");
      return;
    }

    // Create recognition instance
    const recognition = new SpeechRecognition();

    // CRITICAL CONFIG: Prevents repetition and looping
    recognition.continuous = true; // Keep listening until manually stopped
    recognition.interimResults = true; // Enable real-time transcription
    recognition.maxAlternatives = 1; // Only get best result
    recognition.lang = "en-US"; // Language

    // Event: Recognition starts
    recognition.onstart = () => {
      console.log("[VoiceRecorder] Recognition started");
      isListeningRef.current = true;
      setIsListening(true);
      setError(null);
      lastFinalTranscriptRef.current = "";
      lastSoundTimeRef.current = Date.now();
      onStart?.();
    };

    // Event: Recognition ends
    recognition.onend = () => {
      console.log(
        "[VoiceRecorder] Recognition ended, shouldStop:",
        shouldStopRef.current
      );

      // Only actually stop if we intended to stop
      if (!shouldStopRef.current && isListeningRef.current) {
        console.log(
          "[VoiceRecorder] Recognition ended unexpectedly, restarting..."
        );
        try {
          recognition.start();
          return;
        } catch (e) {
          console.error("[VoiceRecorder] Failed to restart:", e);
        }
      }

      shouldStopRef.current = false;
      isListeningRef.current = false;
      setIsListening(false);
      setInterimTranscript("");

      // Cleanup audio monitoring
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      if (microphoneStreamRef.current) {
        microphoneStreamRef.current
          .getTracks()
          .forEach((track) => track.stop());
        microphoneStreamRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      analyserRef.current = null;
      setVolumeLevel(0);

      onStop?.();
    };

    // Event: Recognition error
    recognition.onerror = (event: any) => {
      console.error("[VoiceRecorder] Recognition error:", event.error);
      const errorMessage = getErrorMessage(event.error);
      setError(errorMessage);

      // Auto-dismiss error after 1 second
      setTimeout(() => setError(null), 1000);

      isListeningRef.current = false;
      setIsListening(false);

      // Cleanup audio monitoring
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      if (microphoneStreamRef.current) {
        microphoneStreamRef.current
          .getTracks()
          .forEach((track) => track.stop());
        microphoneStreamRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      analyserRef.current = null;
      setVolumeLevel(0);

      onError?.(errorMessage);
    };

    // Event: Recognition results (MOST IMPORTANT)
    recognition.onresult = (event: any) => {
      let interim = "";
      let final = "";

      // Process all results from this event
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      // Handle FINAL transcript (user finished speaking a sentence)
      if (final.trim() && final !== lastFinalTranscriptRef.current) {
        console.log("[VoiceRecorder] Final transcript:", final);
        lastFinalTranscriptRef.current = final;

        // Update state
        setFinalTranscript(final.trim());
        setInterimTranscript("");

        // Callback to parent
        onFinal?.(final.trim());

        // Reset silence timer
        lastSoundTimeRef.current = Date.now();
      }
      // Handle INTERIM transcript (user still speaking)
      else if (interim.trim()) {
        console.log("[VoiceRecorder] Interim transcript:", interim);
        setInterimTranscript(interim.trim());
        onInterim?.(interim.trim());

        // Reset silence timer
        lastSoundTimeRef.current = Date.now();
      }
    };

    recognitionRef.current = recognition;

    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore cleanup errors
        }
      }
      stopAudioMonitoring();
    };
  }, [onFinal, onInterim, onStart, onStop, onError]);

  /**
   * Get human-readable error message
   */
  const getErrorMessage = (errorCode: string): string => {
    const errorMessages: Record<string, string> = {
      "no-speech": "No speech detected. Please try again.",
      "audio-capture": "Microphone not accessible. Please check permissions.",
      "not-allowed": "Microphone permission denied.",
      network: "Network error. Please check your connection.",
      aborted: "Recording was aborted.",
    };
    return errorMessages[errorCode] || `Recognition error: ${errorCode}`;
  };

  /**
   * Start audio monitoring for volume detection and waveform
   */
  const startAudioMonitoring = async () => {
    try {
      // Request microphone access with echo cancellation
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      microphoneStreamRef.current = stream;

      // Create audio context
      const audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
      audioContextRef.current = audioContext;

      // Create analyser node
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      analyserRef.current = analyser;

      // Connect microphone to analyser
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);

      // Start monitoring volume
      monitorVolume();

      console.log("[VoiceRecorder] Audio monitoring started");
    } catch (error) {
      console.error("[VoiceRecorder] Failed to start audio monitoring:", error);
      setError("Failed to access microphone");
    }
  };

  /**
   * Monitor audio volume level (for auto-stop and waveform)
   */
  const monitorVolume = () => {
    if (!analyserRef.current) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const checkVolume = () => {
      // Use ref instead of state to avoid stale closure
      if (!isListeningRef.current) {
        return;
      }

      analyser.getByteFrequencyData(dataArray);

      // Calculate average volume (0-1 range)
      const average =
        dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
      const normalizedVolume = average / 255;

      setVolumeLevel(normalizedVolume);

      // Auto-stop on silence detection
      if (autoStopOnSilence) {
        if (normalizedVolume < silenceThreshold) {
          const silenceDurationMs = Date.now() - lastSoundTimeRef.current;
          if (silenceDurationMs > silenceDuration) {
            console.log("[VoiceRecorder] Silence detected, auto-stopping");
            if (recognitionRef.current && isListeningRef.current) {
              shouldStopRef.current = true;
              recognitionRef.current.stop();
            }
            return;
          }
        } else {
          lastSoundTimeRef.current = Date.now();
        }
      }

      animationFrameRef.current = requestAnimationFrame(checkVolume);
    };

    checkVolume();
  };

  /**
   * Stop audio monitoring and cleanup
   */
  const stopAudioMonitoring = useCallback(() => {
    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Stop microphone stream
    if (microphoneStreamRef.current) {
      microphoneStreamRef.current.getTracks().forEach((track) => track.stop());
      microphoneStreamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setVolumeLevel(0);

    console.log("[VoiceRecorder] Audio monitoring stopped");
  }, []);

  /**
   * Start voice recording
   */
  const start = useCallback(() => {
    if (!recognitionRef.current) {
      console.warn("[VoiceRecorder] Recognition not initialized");
      setError("Voice recognition not available");
      return;
    }

    if (isListening) {
      console.warn("[VoiceRecorder] Already listening");
      return;
    }

    try {
      // Clear previous state
      setFinalTranscript("");
      setInterimTranscript("");
      setError(null);
      lastFinalTranscriptRef.current = "";
      shouldStopRef.current = false;

      // Start recognition
      recognitionRef.current.start();

      // Start audio monitoring for volume/waveform
      startAudioMonitoring();

      console.log("[VoiceRecorder] Started successfully");
    } catch (error) {
      console.error("[VoiceRecorder] Failed to start:", error);
      setError("Failed to start voice recognition");
      setIsListening(false);
    }
  }, [isListening]);

  /**
   * Stop voice recording
   */
  const stop = useCallback(() => {
    console.log(
      "[VoiceRecorder] Stop called, isListening:",
      isListeningRef.current
    );

    if (!recognitionRef.current) {
      console.warn("[VoiceRecorder] Recognition not initialized");
      return;
    }

    if (!isListeningRef.current) {
      console.warn("[VoiceRecorder] Already stopped");
      return;
    }

    try {
      console.log("[VoiceRecorder] Calling recognition.stop()");
      recognitionRef.current.stop();
      console.log("[VoiceRecorder] Stop requested successfully");
    } catch (error) {
      console.error("[VoiceRecorder] Failed to stop:", error);
      // Force cleanup even if stop fails
      isListeningRef.current = false;
      setIsListening(false);
      stopAudioMonitoring();
    }
  }, [stopAudioMonitoring]);

  return {
    start,
    stop,
    isListening,
    interimTranscript,
    finalTranscript,
    volumeLevel,
    error,
    isSupported,
  };
};

/**
 * Get analyser data for waveform visualization
 */
export const useWaveformData = (
  analyser: AnalyserNode | null,
  isActive: boolean
): Uint8Array => {
  const [waveformData, setWaveformData] = useState<Uint8Array>(
    new Uint8Array(0)
  );

  useEffect(() => {
    if (!analyser || !isActive) {
      setWaveformData(new Uint8Array(0));
      return;
    }

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const updateWaveform = () => {
      analyser.getByteFrequencyData(dataArray);
      setWaveformData(new Uint8Array(dataArray));
      requestAnimationFrame(updateWaveform);
    };

    updateWaveform();
  }, [analyser, isActive]);

  return waveformData;
};

export default useVoiceRecorder;
