import React, { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("Łączenie z API...");

  useEffect(() => {
    // Testujemy połączenie z Twoim backendem FastAPI
    fetch(process.env.REACT_APP_API_URL || "http://localhost:8000")
      .then((res) => res.json())
      .then((data) => setStatus("Połączono z Backendem! ✅"))
      .catch((err) => setStatus("Błąd połączenia z Backendem ❌"));
  }, []);

  return (
    <div
      style={{ textAlign: "center", marginTop: "50px", fontFamily: "Arial" }}
    >
      <h1>AI Business Intelligence Dashboard</h1>
      <p>
        Status systemu: <strong>{status}</strong>
      </p>
      <div style={{ display: "flex", justifyContent: "center", gap: "20px" }}>
        <button onClick={() => window.open("http://localhost:5678", "_blank")}>
          Otwórz n8n
        </button>
        <button
          onClick={() => window.open("http://localhost:8000/docs", "_blank")}
        >
          Dokumentacja API
        </button>
      </div>
    </div>
  );
}

export default App;
