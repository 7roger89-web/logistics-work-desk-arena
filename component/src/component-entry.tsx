// ============================================================================
// Streamlit Components v2 entry point (SINGLE component root).
//
// Streamlit invokes this default export once on mount and again whenever the
// Python side delivers new `data` (same element id → same DOM → route/tab
// state survive backend rerenders). We never remount React on data updates.
//
// Browser-only build: no Node globals (no process/Buffer/require/__dirname).
// ============================================================================

import { Component, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { applyViewModel, type ViewModel } from "./lib/viewmodel";
import { bindTransport } from "./lib/dispatcher";
import App from "./App";
import { ensureFonts } from "./fonts";
import "./index.css";
import "./shell.css";

interface ComponentApi {
  name: string;
  data: ViewModel | null;
  parentElement: ParentNode & Node;
  setTriggerValue: (event: string, value: unknown) => void;
}

/** Safe boundary: a render failure shows a bounded error state, never a blank. */
class Boundary extends Component<{ children: ReactNode }, { error: unknown }> {
  state = { error: null as unknown };
  static getDerivedStateFromError(error: unknown) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, fontFamily: "inherit" }}>
          <div
            style={{
              border: "2px solid #fca5a5",
              background: "#fef2f2",
              borderRadius: 16,
              padding: 20,
              textAlign: "center",
              color: "#991b1b",
            }}
          >
            <p style={{ fontWeight: 800, fontSize: 16, margin: 0 }}>
              Logi-good shell gặp lỗi khi render
            </p>
            <p style={{ fontSize: 13.5, margin: "8px 0 0", opacity: 0.8 }}>
              Nạp lại trang Streamlit để khôi phục. Lỗi:{" "}
              {String(this.state.error)}
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

let root: Root | null = null;
let host: HTMLElement | null = null;

function ensureHostBleedStyle(): void {
  if (typeof document === "undefined" || !document.head) return;
  if (document.getElementById("logi-host-bleed")) return;
  const style = document.createElement("style");
  style.id = "logi-host-bleed";
  style.textContent = `
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    #MainMenu,
    footer {
      display: none !important;
    }
    .stApp {
      background: #EDF1F5 !important;
    }
    .stMainBlockContainer,
    div[data-testid="stAppViewBlockContainer"],
    div[data-testid="stMainBlockContainer"],
    .block-container {
      padding-top: 0 !important;
      padding-bottom: 0 !important;
      padding-left: 0 !important;
      padding-right: 0 !important;
      max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"] > div {
      gap: 0 !important;
    }
  `;
  document.head.appendChild(style);
}

function ensureHost(parent: ParentNode & Node): HTMLElement {
  if (host && parent.contains(host)) return host;
  host = document.createElement("div");
  host.className = "logi-shell";
  parent.appendChild(host);
  return host;
}

export default function mountLogiShell(api: ComponentApi): () => void {
  // (Re)bind the v2 trigger transport for this invocation.
  bindTransport(api.setTriggerValue ?? null);

  ensureFonts();
  ensureHostBleedStyle();
  const h = ensureHost(api.parentElement);
  if (!root) {
    root = createRoot(h);
    root.render(
      <Boundary>
        <App />
      </Boundary>
    );
  }
  if (api.data && typeof api.data === "object") {
    applyViewModel(api.data);
  }
  // Until the first payload arrives, App renders a bounded loading state.

  return () => {
    try {
      root?.unmount();
    } catch {
      // ignore unmount races
    }
    root = null;
    try {
      host?.remove();
    } catch {
      // ignore
    }
    host = null;
    bindTransport(null);
  };
}
