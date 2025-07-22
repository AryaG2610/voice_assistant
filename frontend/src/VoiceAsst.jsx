// src/VoiceAssistant.jsx
import React, { useState } from "react";

export default function VoiceAssistant() {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState("Idle");

  const handleListen = async () => {
    setStatus("Listening...");
    try {
      const res = await fetch("http://127.0.0.1:5000/listen");
      const data = await res.json();
      setCommand(data.command);
      setResponse(data.response);
      setStatus("Idle");
    } catch (err) {
        console.error(err);
        setResponse("Error contacting backend.");
        setStatus("Error");
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 border shadow rounded space-y-4">
      <h1 className="text-2xl font-bold">🎙️ Voice Assistant</h1>
      <button
        onClick={handleListen}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        Start Listening
      </button>
      <p><strong>Status:</strong> {status}</p>
      <p><strong>Command:</strong> {command}</p>
      <p><strong>Response:</strong> {response}</p>
    </div>
  );
}
