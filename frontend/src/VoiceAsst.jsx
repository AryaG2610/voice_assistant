import React, { useState } from "react";
import "./App.css"; // Make sure this is imported

export default function VoiceAssistant() {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState("Idle");

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

        <div className="va-status">{statusText}</div>

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
