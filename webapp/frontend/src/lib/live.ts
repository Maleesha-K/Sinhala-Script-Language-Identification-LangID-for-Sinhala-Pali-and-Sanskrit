"use client";

import { useEffect, useRef } from "react";
import axios from "axios";

// ws(s)://host/api/v1 derived from the REST base URL.
const WS_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/^http/, "ws");

const MAX_RETRY_MS = 10_000;

export type LiveEvent = { type: string; [key: string]: unknown };

type Options = {
  /** Socket path below /api/v1, e.g. `/ws/documents/<id>`. */
  path: string;
  /** Connect only while true, e.g. while the job is still running. */
  enabled: boolean;
  /** Load the current state over REST. Called once the socket listens. */
  load: () => Promise<void>;
  /** Apply one event to the loaded state. Events carry absolute values, so
   * applying one the REST state already reflects is harmless. */
  onEvent: (event: LiveEvent) => void;
  /** True when the event means nothing more will come. */
  isFinal: (event: LiveEvent) => boolean;
};

/**
 * Follows a backend progress socket (see backend app/utils/events.py).
 *
 * The server sends `subscribed` once it listens on Redis; the state is loaded
 * over REST after that, and events that arrive during the load are applied
 * after it, so no update is lost or applied out of order. A dropped
 * connection reconnects (and reloads) with backoff until a final event.
 */
export function useLiveChannel({ path, enabled, load, onEvent, isFinal }: Options) {
  // The socket outlives renders; it always calls the latest callbacks.
  const handlers = useRef({ load, onEvent, isFinal });
  useEffect(() => {
    handlers.current = { load, onEvent, isFinal };
  });

  useEffect(() => {
    if (!enabled) return;
    let stopped = false;
    let finished = false;
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let retryMs = 1000;

    const connect = async () => {
      let token: string;
      try {
        // Access tokens live 15 minutes, so fetch a fresh one per connection.
        token = (await axios.get("/api/auth/token")).data.token;
      } catch {
        scheduleRetry();
        return;
      }
      if (stopped) return;

      let buffer: LiveEvent[] | null = null; // events received while loading
      const ws = new WebSocket(`${WS_URL}${path}?token=${encodeURIComponent(token)}`);
      socket = ws;

      const apply = (event: LiveEvent) => {
        handlers.current.onEvent(event);
        if (handlers.current.isFinal(event)) finished = true;
      };

      ws.onmessage = async (message) => {
        let event: LiveEvent;
        try {
          event = JSON.parse(message.data);
        } catch {
          return;
        }
        if (event.type === "subscribed") {
          retryMs = 1000;
          buffer = [];
          try {
            await handlers.current.load();
          } finally {
            const pending = buffer ?? [];
            buffer = null;
            pending.forEach(apply);
          }
          return;
        }
        if (buffer) buffer.push(event);
        else apply(event);
      };

      ws.onclose = (close) => {
        socket = null;
        // 1008: rejected (bad token, not ours, unknown id); retrying won't help.
        if (stopped || finished || close.code === 1008) return;
        scheduleRetry();
      };
    };

    const scheduleRetry = () => {
      if (stopped) return;
      retryTimer = setTimeout(connect, retryMs);
      retryMs = Math.min(retryMs * 2, MAX_RETRY_MS);
    };

    connect();
    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, [path, enabled]);
}
