import React, { useState, useEffect, useRef, useCallback } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { X, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAppContext } from "@/context/AppContext";

interface VoiceChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export default function VoiceChatModal({ isOpen, onClose }: VoiceChatModalProps) {
  const { refreshChats } = useAppContext();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [statusText, setStatusText] = useState("Initializing...");
  
  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const conversationCreatedRef = useRef(false);
  const autoStartedRef = useRef(false);

  // Volume level monitoring
  const startVolumeMonitoring = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;
      
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      
      const updateVolume = () => {
        if (analyserRef.current && isListening) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setVolumeLevel(average / 255);
          animationFrameRef.current = requestAnimationFrame(updateVolume);
        }
      };
      
      updateVolume();
    } catch (err) {
      console.error("Failed to start volume monitoring:", err);
    }
  }, [isListening]);

  // Stop volume monitoring
  const stopVolumeMonitoring = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setVolumeLevel(0);
  }, []);

  // Initialize speech recognition and AUTO-START
  useEffect(() => {
    if (!isOpen) return;
    
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setError("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      setStatusText("Not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: any) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        handleUserMessage(finalTranscript.trim());
        setCurrentTranscript("");
      } else {
        setCurrentTranscript(interimTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      if (event.error === "not-allowed") {
        setError("Microphone access denied. Please allow microphone access.");
        setStatusText("Access denied");
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      if (isListening && !isProcessing) {
        try {
          recognition.start();
        } catch (e) {
          console.log("Recognition restart failed");
        }
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      stopVolumeMonitoring();
    };
  }, [isOpen, isListening, isProcessing, stopVolumeMonitoring]);

  // Create conversation and AUTO-START listening when modal opens
  useEffect(() => {
    if (isOpen && !conversationId && !conversationCreatedRef.current && !isCreatingConversation) {
      conversationCreatedRef.current = true;
      setIsCreatingConversation(true);
      setError(null);
      setStatusText("Starting...");
      
      api.chats.create({ title: "Agent Chat" })
        .then((response) => {
          if (response?.conversation_id) {
            setConversationId(response.conversation_id);
            console.log("[VoiceChatModal] Created conversation:", response.conversation_id);
            
            // AUTO-START microphone after conversation is created
            if (!autoStartedRef.current && recognitionRef.current) {
              autoStartedRef.current = true;
              setTimeout(() => {
                try {
                  recognitionRef.current.start();
                  setIsListening(true);
                  setStatusText("Listening...");
                  startVolumeMonitoring();
                } catch (e) {
                  console.error("Failed to auto-start:", e);
                }
              }, 500);
            }
          } else {
            throw new Error("No conversation ID returned");
          }
        })
        .catch((err) => {
          console.error("Failed to create voice chat conversation:", err);
          setError("Failed to start voice chat. Please try again.");
          setStatusText("Failed to start");
          conversationCreatedRef.current = false;
        })
        .finally(() => {
          setIsCreatingConversation(false);
        });
    }
  }, [isOpen, conversationId, isCreatingConversation, startVolumeMonitoring]);

  const handleUserMessage = useCallback(async (text: string) => {
    if (!text.trim() || !conversationId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      isUser: true,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsProcessing(true);
    setStatusText("Thinking...");

    try {
      let fullResponse = "";
      
      for await (const chunk of api.chats.askStream({
        conversation_id: conversationId,
        message: text.trim(),
      })) {
        if (chunk.type === "content" && chunk.text) {
          fullResponse += chunk.text;
        }
      }

      if (fullResponse) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: fullResponse,
          isUser: false,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        speakText(fullResponse);
      }
    } catch (err) {
      console.error("Error getting response:", err);
      setError("Failed to get response. Please try again.");
    } finally {
      setIsProcessing(false);
      setStatusText("Listening...");
    }
  }, [conversationId]);

  const speakText = (text: string) => {
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();
    setStatusText("Speaking...");
    setIsSpeaking(true);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(
      (v) => v.name.includes("Google") || v.name.includes("Natural") || v.lang.startsWith("en")
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onend = () => {
      setIsSpeaking(false);
      setStatusText("Listening...");
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      setStatusText("Listening...");
    };

    window.speechSynthesis.speak(utterance);
  };

  const handleClose = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    window.speechSynthesis.cancel();
    stopVolumeMonitoring();
    setIsListening(false);
    setIsSpeaking(false);
    setMessages([]);
    setCurrentTranscript("");
    setConversationId(null);
    setError(null);
    conversationCreatedRef.current = false;
    autoStartedRef.current = false;
    
    refreshChats(true).catch(console.error);
    onClose();
  };

  // Calculate ripple sizes based on volume
  const baseSize = 120;
  const ripple1 = baseSize + (volumeLevel * 80);
  const ripple2 = baseSize + (volumeLevel * 120);
  const ripple3 = baseSize + (volumeLevel * 160);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="bg-gradient-to-b from-gray-900 to-black border-gray-800 text-gray-100 max-w-md p-0 overflow-hidden">
        {/* Close button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={handleClose}
          className="absolute right-4 top-4 z-10 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-full"
        >
          <X className="w-5 h-5" />
        </Button>

        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
          {/* Error display */}
          {error && (
            <div className="absolute top-16 left-4 right-4 bg-red-900/50 border border-red-700 rounded-lg p-3 text-sm text-red-300">
              {error}
            </div>
          )}

          {/* Current transcript */}
          {currentTranscript && (
            <div className="absolute top-20 left-4 right-4 text-center">
              <p className="text-gray-300 text-lg italic">"{currentTranscript}"</p>
            </div>
          )}

          {/* ChatGPT-style animated orb */}
          <div className="relative flex items-center justify-center">
            {/* Outer ripples - appear when listening */}
            {isListening && (
              <>
                <div 
                  className="absolute rounded-full bg-blue-500/10 transition-all duration-150"
                  style={{ 
                    width: ripple3, 
                    height: ripple3,
                    opacity: 0.3 + volumeLevel * 0.3 
                  }}
                />
                <div 
                  className="absolute rounded-full bg-blue-500/20 transition-all duration-150"
                  style={{ 
                    width: ripple2, 
                    height: ripple2,
                    opacity: 0.4 + volumeLevel * 0.3 
                  }}
                />
                <div 
                  className="absolute rounded-full bg-blue-500/30 transition-all duration-150"
                  style={{ 
                    width: ripple1, 
                    height: ripple1,
                    opacity: 0.5 + volumeLevel * 0.3 
                  }}
                />
              </>
            )}

            {/* Speaking animation */}
            {isSpeaking && (
              <>
                <div className="absolute w-40 h-40 rounded-full bg-cyan-500/20 animate-ping" />
                <div className="absolute w-36 h-36 rounded-full bg-cyan-500/30 animate-pulse" />
              </>
            )}

            {/* Processing animation */}
            {isProcessing && (
              <div className="absolute w-32 h-32 rounded-full border-4 border-cyan-500/50 border-t-cyan-500 animate-spin" />
            )}

            {/* Main orb */}
            <div 
              className={`relative w-28 h-28 rounded-full flex items-center justify-center transition-all duration-300 ${
                isListening 
                  ? "bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 shadow-2xl shadow-blue-500/50" 
                  : isSpeaking
                  ? "bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-500 shadow-2xl shadow-cyan-500/50"
                  : isProcessing
                  ? "bg-gradient-to-br from-gray-600 to-gray-700"
                  : "bg-gradient-to-br from-gray-700 to-gray-800"
              }`}
              style={{
                transform: isListening ? `scale(${1 + volumeLevel * 0.15})` : 'scale(1)'
              }}
            >
              {/* Inner glow */}
              <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white/20 to-transparent" />
              
              {/* Icon or waveform */}
              {isProcessing ? (
                <Loader2 className="w-10 h-10 text-white animate-spin" />
              ) : (
                <div className="flex items-end gap-1 h-10">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1.5 bg-white rounded-full transition-all duration-100"
                      style={{
                        height: isListening || isSpeaking
                          ? `${Math.max(8, (volumeLevel * 40) + Math.sin(Date.now() / 100 + i) * 10)}px`
                          : '8px',
                        opacity: isListening || isSpeaking ? 1 : 0.5
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Status text */}
          <p className={`mt-8 text-lg font-medium transition-all ${
            isListening ? "text-blue-400" : isSpeaking ? "text-cyan-400" : "text-gray-400"
          }`}>
            {statusText}
          </p>

          {/* Last message preview */}
          {messages.length > 0 && (
            <div className="mt-6 max-w-full px-4">
              <p className="text-sm text-gray-500 text-center truncate">
                {messages[messages.length - 1].isUser ? "You: " : "Agent: "}
                {messages[messages.length - 1].text.slice(0, 50)}
                {messages[messages.length - 1].text.length > 50 ? "..." : ""}
              </p>
            </div>
          )}

          {/* Instructions */}
          <p className="absolute bottom-6 text-xs text-gray-600 text-center px-4">
            Speak naturally • I'll respond with voice
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
