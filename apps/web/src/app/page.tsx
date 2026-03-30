'use client';

import { useState, useRef, useEffect } from 'react';
import { Camera, CameraOff, Volume2, Settings, RotateCcw, ShieldQuestion } from 'lucide-react';
import { cn } from '@/lib/utils';

type InputMode = 'letters' | 'words';

export default function Home() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [currentChar, setCurrentChar] = useState('');
  const [inputMode, setInputMode] = useState<InputMode>('letters');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [overlayLandmarks, setOverlayLandmarks] = useState<number[][]>([]);
  const [geminiCorrectedText, setGeminiCorrectedText] = useState('');
  const [geminiMeta, setGeminiMeta] = useState<{ empty?: boolean; finishReason?: string } | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [murfApiKey, setMurfApiKey] = useState('');
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [murfKeyStatus, setMurfKeyStatus] = useState<'idle' | 'testing' | 'ok' | 'error'>('idle');
  const [geminiKeyStatus, setGeminiKeyStatus] = useState<'idle' | 'testing' | 'ok' | 'error'>('idle');
  const [murfKeyMsg, setMurfKeyMsg] = useState<string>('');
  const [geminiKeyMsg, setGeminiKeyMsg] = useState<string>('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const lastSpokenTextRef = useRef<string>('');
  const speakRequestIdRef = useRef<number>(0);
  const geminiCooldownUntilMsRef = useRef<number>(0);
  const lastTranscriptRef = useRef<string>('');
  const lastAutoSpokenTranscriptRef = useRef<string>('');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const isSendingFrameRef = useRef<boolean>(false);
  const lastSentFrameSizeRef = useRef<{ w: number; h: number } | null>(null);
  const frameIdRef = useRef<number>(0);
  const inflightFrameIdRef = useRef<number | null>(null);

  useEffect(() => {
    try {
      const mk = window.localStorage.getItem('handtalk_murf_api_key') || '';
      const gk = window.localStorage.getItem('handtalk_gemini_api_key') || '';
      setMurfApiKey(mk);
      setGeminiApiKey(gk);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem('handtalk_murf_api_key', murfApiKey);
    } catch {
      // ignore
    }
  }, [murfApiKey]);

  useEffect(() => {
    try {
      window.localStorage.setItem('handtalk_gemini_api_key', geminiApiKey);
    } catch {
      // ignore
    }
  }, [geminiApiKey]);

  const verifyMurfKey = async () => {
    setMurfKeyStatus('testing');
    setMurfKeyMsg('Testing…');
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(murfApiKey ? { 'x-murf-api-key': murfApiKey } : {}),
        },
        body: JSON.stringify({ text: 'test' }),
      });

      if (res.ok) {
        const ct = res.headers.get('content-type') || '';
        if (ct.includes('audio')) {
          setMurfKeyStatus('ok');
          setMurfKeyMsg('Murf key is valid');
        } else {
          setMurfKeyStatus('error');
          setMurfKeyMsg('Unexpected response from Murf');
        }
        return;
      }

      setMurfKeyStatus('error');
      if (res.status === 400) setMurfKeyMsg('Missing Murf key');
      else if (res.status === 401 || res.status === 403) setMurfKeyMsg('Invalid Murf key');
      else if (res.status === 429) setMurfKeyMsg('Murf quota/rate limit reached');
      else setMurfKeyMsg(`Murf error (${res.status})`);
    } catch (e) {
      setMurfKeyStatus('error');
      setMurfKeyMsg('Network error while testing Murf');
    }
  };

  const verifyGeminiKey = async () => {
    setGeminiKeyStatus('testing');
    setGeminiKeyMsg('Testing…');
    try {
      const res = await fetch('/api/gemini', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(geminiApiKey ? { 'x-gemini-api-key': geminiApiKey } : {}),
        },
        body: JSON.stringify({ text: 'hello' }),
      });

      if (res.ok) {
        setGeminiKeyStatus('ok');
        setGeminiKeyMsg('Gemini key is valid');
        return;
      }

      setGeminiKeyStatus('error');
      if (res.status === 400) setGeminiKeyMsg('Missing Gemini key');
      else if (res.status === 401 || res.status === 403) setGeminiKeyMsg('Invalid Gemini key');
      else if (res.status === 429) setGeminiKeyMsg('Gemini quota/rate limit reached');
      else setGeminiKeyMsg(`Gemini error (${res.status})`);
    } catch (e) {
      setGeminiKeyStatus('error');
      setGeminiKeyMsg('Network error while testing Gemini');
    }
  };

  const startCamera = async () => {
    try {
      if (!audioCtxRef.current) {
        const AC: any = (window as any).AudioContext || (window as any).webkitAudioContext;
        if (AC) audioCtxRef.current = new AC();
      }
      try {
        await audioCtxRef.current?.resume();
      } catch {
        // ignore
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
        },
      });
      streamRef.current = stream;
      setIsStreaming(true);
    } catch (err) {
      console.error('Failed to access camera:', err);
      alert('Please allow camera access to use sign language recognition.');
    }
  };

  const stopCamera = () => {
    const stream = streamRef.current;
    if (stream) stream.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    lastAutoSpokenTranscriptRef.current = '';
    setIsStreaming(false);
  };

  useEffect(() => {
    if (!videoRef.current) return;

    if (isStreaming && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      void videoRef.current.play().catch(() => {
        // Some browsers require a user gesture; the Start Camera click is usually enough.
      });
    } else {
      videoRef.current.srcObject = null;
    }
  }, [isStreaming]);

  useEffect(() => {
    if (!isStreaming) return;

    let rafId = 0;

    const draw = () => {
      const video = videoRef.current;
      const canvas = overlayCanvasRef.current;
      if (!video || !canvas) {
        rafId = window.requestAnimationFrame(draw);
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        rafId = window.requestAnimationFrame(draw);
        return;
      }

      const w = video.videoWidth;
      const h = video.videoHeight;
      if (!w || !h) {
        rafId = window.requestAnimationFrame(draw);
        return;
      }

      if (canvas.width !== w) canvas.width = w;
      if (canvas.height !== h) canvas.height = h;
      ctx.clearRect(0, 0, w, h);

      const pts = overlayLandmarks;
      if (Array.isArray(pts) && pts.length === 21) {
        ctx.strokeStyle = 'rgba(0, 255, 0, 0.9)';
        ctx.lineWidth = 3;
        ctx.fillStyle = 'rgba(255, 0, 0, 0.9)';

        const pairs: Array<[number, number]> = [
          [0, 1], [1, 2], [2, 3], [3, 4],
          [0, 5], [5, 6], [6, 7], [7, 8],
          [0, 9], [9, 10], [10, 11], [11, 12],
          [0, 13], [13, 14], [14, 15], [15, 16],
          [0, 17], [17, 18], [18, 19], [19, 20],
          [5, 9], [9, 13], [13, 17],
        ];

        for (const [a, b] of pairs) {
          const pa = pts[a];
          const pb = pts[b];
          if (!pa || !pb) continue;
          ctx.beginPath();
          ctx.moveTo(pa[0], pa[1]);
          ctx.lineTo(pb[0], pb[1]);
          ctx.stroke();
        }

        for (const p of pts) {
          if (!p) continue;
          ctx.beginPath();
          ctx.arc(p[0], p[1], 3, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      rafId = window.requestAnimationFrame(draw);
    };

    rafId = window.requestAnimationFrame(draw);
    return () => window.cancelAnimationFrame(rafId);
  }, [isStreaming, overlayLandmarks]);

  const playTTS = async (text: string) => {
    const t = text.trim();
    if (!t) return;
    setIsSpeaking(true);
    try {
      try {
        await audioCtxRef.current?.resume();
      } catch {
        // ignore
      }

      if (audioRef.current) {
        try {
          audioRef.current.pause();
          audioRef.current.src = '';
        } catch {
          // ignore
        }
        audioRef.current = null;
      }

      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(murfApiKey ? { 'x-murf-api-key': murfApiKey } : {}),
        },
        body: JSON.stringify({ text: t }),
      });
      if (res.ok) {
        const audioBlob = await res.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          if (audioRef.current === audio) audioRef.current = null;
          setIsSpeaking(false);
        };
        try {
          await audio.play();
        } catch (e) {
          // Autoplay might be blocked until the user interacts with the page.
          URL.revokeObjectURL(audioUrl);
          if (audioRef.current === audio) audioRef.current = null;
          setIsSpeaking(false);
          console.warn('Audio play blocked by browser autoplay policy:', e);
        }
      } else {
        setIsSpeaking(false);
        let msg = 'Failed to generate speech';
        try {
          const j = (await res.json()) as any;
          if (res.status === 400) msg = 'Add your Murf API key in Settings';
          else if (res.status === 401 || res.status === 403) msg = 'Invalid Murf API key';
          else if (res.status === 429) msg = 'Murf quota/rate limit reached';
          else if (typeof j?.error === 'string') msg = j.error;
        } catch {
          // ignore
        }
        alert(msg);
      }
    } catch (err) {
      console.error(err);
      setIsSpeaking(false);
      alert('Failed to generate speech');
    }
  };

  const speak = async () => {
    await playTTS(transcript);
  };

  const speakGemini = async () => {
    await playTTS(geminiCorrectedText || transcript);
  };

  useEffect(() => {
    if (!isStreaming) return;
    if (!wsConnected) return;

    const raw = transcript.trim();
    if (!raw) return;

    const prevRaw = lastAutoSpokenTranscriptRef.current;
    if (prevRaw && raw === prevRaw) return;

    if (transcript === lastTranscriptRef.current) return;
    lastTranscriptRef.current = transcript;

    if (inputMode === 'words') {
      if (!/[\s.!?]$/.test(transcript)) return;
    }

    if (isSpeaking) return;

    const requestId = ++speakRequestIdRef.current;
    const timeoutId = window.setTimeout(async () => {
      try {
        // Speak only the newly appended part of the transcript.
        const prev = lastAutoSpokenTranscriptRef.current;
        let toSpeak = raw;
        if (prev && raw.startsWith(prev)) {
          toSpeak = raw.slice(prev.length).trim();
        }

        if (!toSpeak) return;

        if (inputMode === 'letters') {
          // Keep letter-mode speech responsive but avoid speaking long bursts.
          toSpeak = toSpeak.slice(-6);
        }

        // Speak immediately (raw transcript) for minimal latency.
        setIsSpeaking(true);
        lastAutoSpokenTranscriptRef.current = raw;
        await playTTS(toSpeak);

        // Gemini correction runs in the background (does not delay Murf).
        // Only do this in 'words' mode to save AI calls.
        const now = Date.now();
        const inCooldown = now < geminiCooldownUntilMsRef.current;
        if (inputMode === 'words' && !inCooldown) {
          void (async () => {
            try {
              const geminiRes = await fetch('/api/gemini', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  ...(geminiApiKey ? { 'x-gemini-api-key': geminiApiKey } : {}),
                },
                body: JSON.stringify({ text: raw }),
              });

              if (geminiRes.ok) {
                const geminiJson = (await geminiRes.json()) as {
                  correctedText?: string;
                  geminiEmpty?: boolean;
                  finishReason?: string;
                };
                const corrected = (geminiJson.correctedText || raw).trim();
                if (requestId !== speakRequestIdRef.current) return;
                if (corrected) setGeminiCorrectedText(corrected);
                setGeminiMeta(geminiJson.geminiEmpty ? { empty: true, finishReason: geminiJson.finishReason } : null);
              } else {
                if (geminiRes.status === 429) {
                  const retryAfterHeader = geminiRes.headers.get('retry-after');
                  const retryAfterSeconds = retryAfterHeader ? Number(retryAfterHeader) : NaN;
                  const backoffMs = Number.isFinite(retryAfterSeconds) ? retryAfterSeconds * 1000 : 30_000;
                  geminiCooldownUntilMsRef.current = Date.now() + Math.max(5_000, backoffMs);
                  setGeminiMeta({ empty: true, finishReason: `rate_limited_${Math.round(Math.max(5_000, backoffMs) / 1000)}s` });
                }
              }
            } catch {
              // ignore
            }
          })();
        }

        if (requestId !== speakRequestIdRef.current) return;
      } catch (err) {
        console.error('Auto speak error:', err);
      } finally {
        if (requestId === speakRequestIdRef.current) {
          setIsSpeaking(false);
        }
      }
    }, 150);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [isStreaming, wsConnected, transcript, isSpeaking, inputMode]);

  const clear = () => {
    setTranscript('');
    setCurrentChar('');
    lastAutoSpokenTranscriptRef.current = '';
  };

  useEffect(() => {
    if (isStreaming) {
      const rawUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8001/ws';
      const wsUrl = rawUrl.startsWith('ws://localhost:') ? rawUrl.replace('ws://localhost:', 'ws://127.0.0.1:') : rawUrl;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => {
        setWsConnected(true);
        console.log('WebSocket connected');
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data && 'frameId' in data && inflightFrameIdRef.current !== null) {
          if (data.frameId === inflightFrameIdRef.current) {
            inflightFrameIdRef.current = null;
          }
        }

        setCurrentChar(typeof data?.currentChar === 'string' ? data.currentChar : '');
        if (typeof data?.transcript === 'string') setTranscript(data.transcript);
        // Always update overlay landmarks; empty array should clear stale overlay
        if (data.overlay && 'landmarks' in data.overlay) {
          const lm = Array.isArray(data.overlay.landmarks) ? data.overlay.landmarks : [];
          const video = videoRef.current;
          const sent = lastSentFrameSizeRef.current;
          if (
            video &&
            sent &&
            sent.w > 0 &&
            sent.h > 0 &&
            video.videoWidth > 0 &&
            video.videoHeight > 0 &&
            lm.length === 21
          ) {
            const sx = video.videoWidth / sent.w;
            const sy = video.videoHeight / sent.h;
            const scaled = lm.map((p: any) => {
              if (!Array.isArray(p) || p.length < 2) return p;
              return [p[0] * sx, p[1] * sy, p[2]];
            });
            setOverlayLandmarks(scaled);
          } else {
            setOverlayLandmarks(lm);
          }
        } else {
          setOverlayLandmarks([]);
        }
      };
      ws.onerror = (err) => console.error('WebSocket error:', err);
      ws.onclose = () => {
        setWsConnected(false);
        console.log('WebSocket closed');
      };
      return () => {
        setWsConnected(false);
        ws.close();
      };
    }
  }, [isStreaming]);

  useEffect(() => {
    if (!isStreaming) return;
    if (!videoRef.current) return;

    let intervalId: number | undefined;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const sendFrame = () => {
      const ws = wsRef.current;
      const video = videoRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      if (!video) return;
      if (video.readyState < 2) return;
      if (isSendingFrameRef.current) return;

      // Only keep one in-flight frame to prevent queueing/latency.
      if (inflightFrameIdRef.current !== null) return;

      // If the WS buffer is growing, drop frames to keep latency low.
      if (ws.bufferedAmount > 250_000) return;

      const width = video.videoWidth;
      const height = video.videoHeight;
      if (!width || !height) return;

      const targetW = Math.min(224, width);
      const scale = targetW / width;
      const targetH = Math.max(1, Math.round(height * scale));

      isSendingFrameRef.current = true;
      try {
        canvas.width = targetW;
        canvas.height = targetH;
        ctx.drawImage(video, 0, 0, targetW, targetH);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.35);
        lastSentFrameSizeRef.current = { w: targetW, h: targetH };

        const frameId = ++frameIdRef.current;
        inflightFrameIdRef.current = frameId;
        const clientTs = Date.now();

        ws.send(
          JSON.stringify({
            image: dataUrl,
            inputMode,
            frameId,
            clientTs,
          })
        );
      } catch (err) {
        console.error('Failed to send frame:', err);
        inflightFrameIdRef.current = null;
      } finally {
        isSendingFrameRef.current = false;
      }
    };

    // Fast tick; actual send rate is gated by one-in-flight ack.
    intervalId = window.setInterval(sendFrame, 50);
    return () => {
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [isStreaming, inputMode]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSettingsOpen(false);
        setHelpOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <main className="min-h-screen bg-black text-gray-100">
      <div className="relative w-screen h-[100svh] overflow-hidden">
        <div className="absolute inset-0 bg-black">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={cn('absolute inset-0 w-full h-full object-cover', !isStreaming && 'hidden')}
            style={{ transform: 'scaleX(-1)' }}
          />
          <canvas
            ref={overlayCanvasRef}
            className={cn('absolute inset-0 w-full h-full', !isStreaming && 'hidden')}
            style={{ transform: 'scaleX(-1)' }}
          />
          {!isStreaming && (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="rounded-3xl bg-white/5 border border-white/10 px-6 py-5 shadow-2xl">
                <div className="flex items-center justify-center gap-3">
                  <CameraOff size={42} />
                  <div className="text-left">
                    <div className="text-lg font-semibold text-white">Camera Off</div>
                    <div className="text-sm text-gray-400">Start the camera to begin recognition</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="absolute inset-x-0 top-0 p-3 sm:p-4 md:p-6" style={{ paddingTop: 'max(12px, env(safe-area-inset-top))' }}>
          <div className="mx-auto max-w-6xl flex items-center justify-between gap-2 sm:gap-3">
            <div className="flex items-center gap-3">
              <div className="text-xl md:text-2xl font-extrabold tracking-tight text-white drop-shadow-[0_0_16px_rgba(255,255,255,0.6)]">
                HandTalk
              </div>
              {currentChar && (
                <div className="hidden sm:flex items-center gap-2 rounded-2xl bg-white/10 ring-1 ring-white/15 px-3 py-1.5">
                  <span className="text-xs text-gray-300">Live</span>
                  <span className="text-lg font-extrabold text-white">{currentChar}</span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setHelpOpen(false);
                  setSettingsOpen((v) => !v);
                }}
                className="inline-flex items-center justify-center gap-2 rounded-2xl px-3 py-2 sm:px-4 sm:py-2.5 text-sm font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 transition min-h-11"
                aria-label="Settings"
              >
                <Settings size={18} strokeWidth={2} />
                <span className="hidden md:inline">Settings</span>
              </button>

              <button
                onClick={() => {
                  setSettingsOpen(false);
                  setHelpOpen((v) => !v);
                }}
                className="inline-flex items-center justify-center gap-2 rounded-2xl px-3 py-2 sm:px-4 sm:py-2.5 text-sm font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 transition min-h-11"
                aria-label="Help"
              >
                <ShieldQuestion size={18} strokeWidth={1.8} />
                <span className="hidden md:inline">Help</span>
              </button>

              <button
                onClick={isStreaming ? stopCamera : startCamera}
                className={cn(
                  'inline-flex items-center justify-center gap-2 rounded-2xl px-3 py-2 sm:px-4 sm:py-2.5 text-sm font-semibold bg-white text-black hover:bg-white/90 transition min-h-11',
                  isStreaming && 'bg-red-500 text-white hover:bg-red-500/90'
                )}
              >
                {isStreaming ? <CameraOff size={18} /> : <Camera size={18} />}
                <span className="hidden md:inline">{isStreaming ? 'Stop' : 'Start'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Settings (desktop dropdown) */}
        {settingsOpen && (
          <>
            <div
              className="hidden sm:block absolute inset-0 z-10"
              onClick={() => setSettingsOpen(false)}
            />
            <div className="hidden sm:block absolute z-20 top-20 right-4 md:right-6 w-80 rounded-2xl bg-zinc-950/95 backdrop-blur border border-white/10 shadow-2xl p-3">
              <div className="space-y-3">
                <div>
                  <div className="text-xs font-semibold text-gray-300 mb-2">Input</div>
                  <div className="grid grid-cols-2 gap-2">
                    {(['letters', 'words'] as const).map((im) => (
                      <button
                        key={im}
                        onClick={() => setInputMode(im)}
                        className={cn(
                          'rounded-xl px-3 py-2 text-sm font-semibold capitalize transition ring-1',
                          inputMode === im
                            ? 'bg-white text-black ring-white/30'
                            : 'bg-white/5 text-white ring-white/10 hover:bg-white/10'
                        )}
                      >
                        {im}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-white/10">
                  <div className="text-xs font-semibold text-gray-300 mb-2">API Keys (saved locally)</div>

                  <div className="space-y-2">
                    <div className="space-y-1">
                      <div className="text-[11px] text-gray-400">Murf API Key</div>
                      <input
                        value={murfApiKey}
                        onChange={(e) => {
                          setMurfApiKey(e.target.value);
                          setMurfKeyStatus('idle');
                          setMurfKeyMsg('');
                        }}
                        type="password"
                        placeholder="Paste Murf key"
                        className="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-sm text-white placeholder:text-gray-500 outline-none focus:border-white/20"
                      />
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-[11px] text-gray-400">{murfKeyMsg}</div>
                        <button
                          onClick={verifyMurfKey}
                          disabled={murfKeyStatus === 'testing' || !murfApiKey}
                          className="rounded-xl px-3 py-2 text-xs font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 disabled:opacity-40 transition"
                        >
                          {murfKeyStatus === 'testing' ? 'Testing…' : murfKeyStatus === 'ok' ? 'Verified' : 'Verify'}
                        </button>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="text-[11px] text-gray-400">Gemini API Key</div>
                      <input
                        value={geminiApiKey}
                        onChange={(e) => {
                          setGeminiApiKey(e.target.value);
                          setGeminiKeyStatus('idle');
                          setGeminiKeyMsg('');
                        }}
                        type="password"
                        placeholder="Paste Gemini key"
                        className="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-sm text-white placeholder:text-gray-500 outline-none focus:border-white/20"
                      />
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-[11px] text-gray-400">{geminiKeyMsg}</div>
                        <button
                          onClick={verifyGeminiKey}
                          disabled={geminiKeyStatus === 'testing' || !geminiApiKey}
                          className="rounded-xl px-3 py-2 text-xs font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 disabled:opacity-40 transition"
                        >
                          {geminiKeyStatus === 'testing' ? 'Testing…' : geminiKeyStatus === 'ok' ? 'Verified' : 'Verify'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-1 flex justify-between text-[11px] text-gray-400">
                  <span>WS: {wsConnected ? 'Connected' : 'Disconnected'}</span>
                  <button
                    onClick={() => setSettingsOpen(false)}
                    className="text-gray-300 hover:text-white transition"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Settings (mobile bottom sheet) */}
        {settingsOpen && (
          <div className="sm:hidden absolute inset-0 z-30">
            <div className="absolute inset-0 bg-black/60" onClick={() => setSettingsOpen(false)} />
            <div
              className="absolute inset-x-0 bottom-0 rounded-t-3xl bg-zinc-950/95 backdrop-blur border-t border-white/10 p-4"
              style={{ paddingBottom: 'max(16px, env(safe-area-inset-bottom))' }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-semibold text-white">Settings</div>
                <button onClick={() => setSettingsOpen(false)} className="text-sm text-gray-300 hover:text-white">Close</button>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="text-xs font-semibold text-gray-300 mb-2">Input</div>
                  <div className="grid grid-cols-2 gap-2">
                    {(['letters', 'words'] as const).map((im) => (
                      <button
                        key={im}
                        onClick={() => setInputMode(im)}
                        className={cn(
                          'rounded-2xl px-3 py-3 text-sm font-semibold capitalize transition ring-1',
                          inputMode === im
                            ? 'bg-white text-black ring-white/30'
                            : 'bg-white/5 text-white ring-white/10 hover:bg-white/10'
                        )}
                      >
                        {im}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-white/10">
                  <div className="text-xs font-semibold text-gray-300 mb-2">API Keys (saved locally)</div>

                  <div className="space-y-3">
                    <div className="space-y-1">
                      <div className="text-[11px] text-gray-400">Murf API Key</div>
                      <input
                        value={murfApiKey}
                        onChange={(e) => {
                          setMurfApiKey(e.target.value);
                          setMurfKeyStatus('idle');
                          setMurfKeyMsg('');
                        }}
                        type="password"
                        placeholder="Paste Murf key"
                        className="w-full rounded-2xl bg-white/5 border border-white/10 px-3 py-3 text-sm text-white placeholder:text-gray-500 outline-none focus:border-white/20"
                      />
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-[11px] text-gray-400">{murfKeyMsg}</div>
                        <button
                          onClick={verifyMurfKey}
                          disabled={murfKeyStatus === 'testing' || !murfApiKey}
                          className="rounded-2xl px-3 py-2 text-xs font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 disabled:opacity-40 transition"
                        >
                          {murfKeyStatus === 'testing' ? 'Testing…' : murfKeyStatus === 'ok' ? 'Verified' : 'Verify'}
                        </button>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="text-[11px] text-gray-400">Gemini API Key</div>
                      <input
                        value={geminiApiKey}
                        onChange={(e) => {
                          setGeminiApiKey(e.target.value);
                          setGeminiKeyStatus('idle');
                          setGeminiKeyMsg('');
                        }}
                        type="password"
                        placeholder="Paste Gemini key"
                        className="w-full rounded-2xl bg-white/5 border border-white/10 px-3 py-3 text-sm text-white placeholder:text-gray-500 outline-none focus:border-white/20"
                      />
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-[11px] text-gray-400">{geminiKeyMsg}</div>
                        <button
                          onClick={verifyGeminiKey}
                          disabled={geminiKeyStatus === 'testing' || !geminiApiKey}
                          className="rounded-2xl px-3 py-2 text-xs font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 disabled:opacity-40 transition"
                        >
                          {geminiKeyStatus === 'testing' ? 'Testing…' : geminiKeyStatus === 'ok' ? 'Verified' : 'Verify'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="text-[11px] text-gray-400">WS: {wsConnected ? 'Connected' : 'Disconnected'}</div>
              </div>
            </div>
          </div>
        )}

        {/* Help (mobile + desktop modal) */}
        {helpOpen && (
          <div className="absolute inset-0 z-30">
            <div className="absolute inset-0 bg-black/60" onClick={() => setHelpOpen(false)} />
            <div
              className="absolute inset-x-0 bottom-0 sm:bottom-auto sm:top-20 sm:right-4 md:right-6 sm:inset-x-auto sm:w-96 rounded-t-3xl sm:rounded-2xl bg-zinc-950/95 backdrop-blur border border-white/10 p-4 shadow-2xl"
              style={{ paddingBottom: 'max(16px, env(safe-area-inset-bottom))' }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-semibold text-white">How to use</div>
                <button onClick={() => setHelpOpen(false)} className="text-sm text-gray-300 hover:text-white">Close</button>
              </div>
              <div className="space-y-2 text-sm text-gray-300">
                <div>1) Tap <span className="text-white font-semibold">Start</span> to enable the camera</div>
                <div>2) Open <span className="text-white font-semibold">Settings</span> and choose Input</div>
                <div>3) Your live text appears as subtitles at the bottom</div>
                <div>4) Voice plays automatically when a word/phrase completes</div>
              </div>
            </div>
          </div>
        )}

        <div className="absolute inset-x-0 bottom-0 p-3 sm:p-4 md:p-6" style={{ paddingBottom: 'max(12px, env(safe-area-inset-bottom))' }}>
          <div className="mx-auto max-w-6xl space-y-3">
            <div className="rounded-3xl bg-gradient-to-t from-black/85 via-black/55 to-black/10 border border-white/10 p-4 md:p-5 shadow-2xl">
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="text-xs font-semibold text-gray-300">Live Transcript</div>
                {geminiMeta?.empty && (
                  <div className="text-[11px] text-gray-400">Gemini: {geminiMeta.finishReason || 'empty'}</div>
                )}
              </div>
              <div className="text-base md:text-lg text-white/95 leading-relaxed">
                {transcript || 'Your live text will appear here as you sign…'}
              </div>
            </div>

            <div className="flex flex-wrap gap-2 justify-center sm:justify-end">
              <button
                onClick={speak}
                disabled={!transcript.trim() || isSpeaking}
                className="inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 sm:py-2 text-sm font-semibold bg-white text-black hover:bg-white/90 disabled:opacity-40 disabled:hover:bg-white transition min-h-11"
              >
                <Volume2 size={18} />
                {isSpeaking ? 'Speaking…' : 'Speak'}
              </button>

              <button
                onClick={speakGemini}
                disabled={!(geminiCorrectedText || transcript).trim() || isSpeaking}
                className="inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 sm:py-2 text-sm font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 disabled:opacity-40 transition min-h-11"
              >
                <Volume2 size={18} />
                Speak Corrected
              </button>

              <button
                onClick={clear}
                className="inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 sm:py-2 text-sm font-semibold bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15 transition min-h-11"
              >
                <RotateCcw size={18} />
                Clear
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
