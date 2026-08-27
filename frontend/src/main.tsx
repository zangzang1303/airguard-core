import React from "react";
import ReactDOM from "react-dom/client";
// Explicit extension avoids Vite resolving the legacy App.jsx entrypoint.
import App from "./App.tsx";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
