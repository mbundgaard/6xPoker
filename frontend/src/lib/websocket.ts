// WebSocket client for game communication
console.log('[WebSocket] Module loading');

export type MessageHandler = (message: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private url: string | null = null;
  private _connectionState: 'disconnected' | 'connecting' | 'connected' = 'disconnected';

  connect(path: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      this.url = `${protocol}//${window.location.host}${path}`;
      this._connectionState = 'connecting';
      this.emit('connection_state', { type: 'connection_state', state: 'connecting' });

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.reconnectAttempts = 0;
          this._connectionState = 'connected';
          this.emit('connection_state', { type: 'connection_state', state: 'connected' });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.emit(message.type, message);
          } catch (e) {
            console.error('Failed to parse message:', event.data);
          }
        };

        this.ws.onclose = () => {
          this._connectionState = 'disconnected';
          this.emit('connection_state', { type: 'connection_state', state: 'disconnected' });
          this.emit('disconnect', { type: 'disconnect' });
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          this._connectionState = 'disconnected';
          reject(error);
        };
      } catch (error) {
        this._connectionState = 'disconnected';
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.url = null;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts || !this.url) {
      return;
    }

    this.reconnectAttempts++;
    setTimeout(() => {
      if (this.url) {
        this.connect(this.url.replace(/^wss?:\/\/[^/]+/, ''));
      }
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  send(type: string, payload: any = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...payload }));
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, []);
    }
    this.handlers.get(type)!.push(handler);
  }

  off(type: string, handler: MessageHandler) {
    const handlers = this.handlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(type: string, message: any) {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.forEach((handler) => handler(message));
    }
    // Also emit to wildcard handlers
    const wildcardHandlers = this.handlers.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => handler(message));
    }
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get connectionState() {
    return this._connectionState;
  }

  clearHandlers() {
    this.handlers.clear();
  }
}

export const wsClient = new WebSocketClient();
console.log('[WebSocket] Client created');
