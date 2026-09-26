/* Speaking to the studio, and being answered.

   The browser's own Web Speech API: no key, no server, nothing uploaded by
   us — though Chrome does send the audio to its own speech service to
   transcribe it, which is worth saying plainly because it means voice needs a
   network connection even though the parsing here does not.

   It holds a conversation rather than taking dictation: the microphone stays
   open, what it hears appears as it hears it, and about a second of silence
   after a complete phrase sends the turn. Four things that matter in this
   domain: numbers are spoken as words and have to become digits before any
   regex sees them, the browser's first guess is not always its most useful
   one, a dropped speech service should be retried rather than ending the
   session, and "stop listening" should stop it. */
import { useCallback, useEffect, useRef, useState } from "react";
import { digitise } from "./assistant";
import { getModel } from "./model";

type SpeechRecognitionLike = {
  lang: string; continuous: boolean; interimResults: boolean; maxAlternatives: number;
  start(): void; stop(): void;
  onresult: ((e: any) => void) | null;
  onerror: ((e: any) => void) | null;
  onend: (() => void) | null;
};

const Recognition = (): (new () => SpeechRecognitionLike) | null =>
  (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;

export const voiceAvailable = () => !!Recognition();

export const LANGUAGES = [
  { code: "en-IN", label: "English" },
  { code: "ta-IN", label: "தமிழ்" },
  { code: "hi-IN", label: "हिन्दी" },
  { code: "ml-IN", label: "മലയാളം" },
];

/** Say something back. Cheap, cancellable, and silent when turned off. */
export function speak(text: string, lang = "en-IN", on = true) {
  if (!on || !window.speechSynthesis || !text) return;
  try {
    const u = new SpeechSynthesisUtterance(String(text).replace(/<[^>]*>/g, "").slice(0, 240));
    u.lang = lang;
    u.rate = 1.02;
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  } catch { /* a browser without synthesis is not a reason to fail */ }
}

/* The browser offers several guesses. Prefer the one the engine can act on:
   a transcript naming a room and a verb beats a better-scoring one naming
   neither. */
function bestAlternative(result: any): string {
  let best = result[0].transcript, bestScore = -Infinity;
  const rooms = getModel().rooms;
  for (let i = 0; i < result.length; i++) {
    const text = digitise(result[i].transcript);
    const padded = " " + text + " ";
    let score = result[i].confidence || 0;
    if (rooms.some(r => padded.includes(" " + r.name.toLowerCase()))) score += 1;
    if (/\b(add|remove|move|make|split|merge|furnish|budget|plot|floor|wider|bigger|keep)\b/.test(padded)) score += 1;
    if (/\d/.test(text)) score += .5;
    if (score > bestScore) { bestScore = score; best = result[i].transcript; }
  }
  return best;
}

export type VoiceState = {
  supported: boolean;
  listening: boolean;
  heard: string;              // what it is hearing right now, including interim words
  error: string;
  toggle: () => void;
  stop: () => void;
};

export function useVoice(lang: string, onTurn: (text: string) => void): VoiceState {
  const [listening, setListening] = useState(false);
  const [heard, setHeard] = useState("");
  const [error, setError] = useState("");
  const rec = useRef<SpeechRecognitionLike | null>(null);
  const final = useRef("");
  const idle = useRef<number | undefined>(undefined);
  const retries = useRef(0);
  const wanted = useRef(false);            // whether the user still wants it open
  const turn = useRef(onTurn);
  turn.current = onTurn;

  const stop = useCallback(() => {
    wanted.current = false;
    try { rec.current?.stop(); } catch { /* already stopped */ }
    setListening(false);
    setHeard("");
  }, []);

  const start = useCallback(() => {
    const SR = Recognition();
    if (!SR) return;
    const r = new SR();
    rec.current = r;
    r.lang = lang;
    r.continuous = true;                   // keep the turn open through a pause
    r.interimResults = true;
    r.maxAlternatives = 3;
    final.current = "";
    retries.current = 0;
    setError("");

    const send = () => {
      const text = final.current.trim();
      final.current = "";
      setHeard("");
      if (!text) return;
      if (/^(stop|stop listening|that'?s all|cancel|never mind)\.?$/i.test(text)) { stop(); return; }
      if (text.replace(/[^a-z0-9]/gi, "").length < 3) return;   // a cough, not an instruction
      turn.current(text);
    };

    r.onresult = (e: any) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        if (res.isFinal) final.current += (final.current ? " " : "") + digitise(bestAlternative(res)).trim();
        else interim += res[0].transcript;
      }
      setHeard((final.current + " " + interim).trim());
      clearTimeout(idle.current);
      // a second of silence after a complete phrase means "go"
      if (final.current) idle.current = setTimeout(send, 1100) as unknown as number;
    };

    r.onerror = (e: any) => {
      if (e.error === "no-speech" || e.error === "aborted") return;
      if (e.error === "network" && wanted.current && retries.current < 3) {
        retries.current++;
        setError("Reconnecting to the speech service…");
        setTimeout(() => { if (wanted.current) { try { r.start(); } catch { /* gone */ } } },
                   800 * retries.current);
        return;
      }
      setError(e.error === "not-allowed"
        ? "Microphone permission was refused — allow it in the address bar and try again."
        : e.error === "network" ? "The browser's speech service could not be reached."
        : String(e.error));
      wanted.current = false;
      setListening(false);
    };

    r.onend = () => {
      clearTimeout(idle.current);
      send();
      if (wanted.current) { try { r.start(); } catch { setListening(false); } }
      else setListening(false);
    };

    try { r.start(); wanted.current = true; setListening(true); }
    catch { setListening(false); }
  }, [lang, stop]);

  // changing language restarts recognition, since it is set when it starts
  useEffect(() => {
    if (!listening) return;
    stop();
    const t = setTimeout(start, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  useEffect(() => () => { wanted.current = false; try { rec.current?.stop(); } catch { /* gone */ } }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && listening) stop(); };
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, [listening, stop]);

  return {
    supported: voiceAvailable(),
    listening, heard, error,
    toggle: () => (listening ? stop() : start()),
    stop,
  };
}
