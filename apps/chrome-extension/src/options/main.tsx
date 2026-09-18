import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App.js";
import "../popup/styles.css";

const root = document.getElementById("root");
if (!root) throw new Error("options root element missing");

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
