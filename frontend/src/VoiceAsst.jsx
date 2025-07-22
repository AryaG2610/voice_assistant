import React, { useState, useEffect } from "react";
import "./App.css";

export default function VoiceAssistant() {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState("Idle");
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  // Load from localStorage and backend on mount
  useEffect(() => {
    const saved = localStorage.getItem("voiceEnabled");
    if (saved !== null) {
      setVoiceEnabled(saved === "true");
      fetch("http://127.0.0.1:5000/toggle-voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: saved === "true" }),
      });
    } else {
      fetch("http://127.0.0.1:5000/get-voice-status")
        .then(res => res.json())
        .then(data => {
          setVoiceEnabled(data.voice_enabled);
          localStorage.setItem("voiceEnabled", String(data.voice_enabled));
        })
        .catch(err => console.error("Failed to get voice status", err));
    }
  }, []);

  const handleListen = async () => {
    setStatus("Listening");
    setCommand("");
    setResponse("");
    try {
      const res = await fetch("http://127.0.0.1:5000/listen");
      const data = await res.json();
      setCommand(data.command || "No command recognized");
      setResponse(data.response || "No response");
      setStatus("Idle");
    } catch (err) {
      console.error(err);
      setResponse("Error contacting backend.");
      setStatus("Error");
    }
  };

  const handleToggleVoice = async () => {
    const newState = !voiceEnabled;
    setVoiceEnabled(newState);
    localStorage.setItem("voiceEnabled", String(newState));
    try {
      await fetch("http://127.0.0.1:5000/toggle-voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: newState }),
      });
    } catch (err) {
      console.error("Error toggling voice:", err);
    }
  };

  const statusText =
    status === "Listening" ? (
      <span className="pulse">🎧 Listening...</span>
    ) : status === "Error" ? (
      <span className="error-text">⚠️ Error</span>
    ) : (
      <span className="idle-text">⏸️ Idle</span>
    );

  return (
    <div className="voiceasst">
      <div className="va-container">
        <h1 className="va-title">🎙️ Voice Assistant</h1>

        <button className="va-button" onClick={handleListen}>
          🎤
        </button>

        <div className="va-status-toggle">
          <div className="va-status">{statusText}</div>
          <button className="va-toggle" onClick={handleToggleVoice}>
            {voiceEnabled ? "🔊 Voice On" : "🔇 Voice Off"}
          </button>
        </div>

        <div className="va-box">
          <p className="va-label">You said:</p>
          <p className="va-content">{command || "—"}</p>
        </div>

        <div className="va-box">
          <p className="va-label">Assistant Response:</p>
          <p className="va-content">{response || "—"}</p>
        </div>
      </div>
    </div>
  );
}
