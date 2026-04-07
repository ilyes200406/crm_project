/**
 * WEBSOCKET SERVICE
 * 
 * Service de connexion WebSocket avec auto-reconnexion
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.url = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000; // 3 seconds
    this.isIntentionallyClosed = false;
    this.heartbeatInterval = null;
    this.token = null; // Store token for reconnection
  }

  /**
   * Connect to WebSocket server
   * 
   * @param {string} token - JWT access token
   */
  connect(token) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    this.isIntentionallyClosed = false;
    this.token = token; // Store for reconnection

    // WebSocket URL (adjust based on your backend config)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || 'localhost:8000';
    this.url = `${protocol}//${host}/ws/notifications/?token=${token}`;

    console.log('[WebSocket] Connecting to:', this.url.replace(token, 'TOKEN'));

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket open
   */
  handleOpen(event) {
    console.log('[WebSocket] Connected successfully');
    this.reconnectAttempts = 0;

    // Start heartbeat
    this.startHeartbeat();

    // Notify listeners
    this.notifyListeners('connected', { timestamp: new Date() });
  }

  /**
   * Handle incoming messages
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log('[WebSocket] Message received:', data);

      // Handle different message types
      switch (data.type) {
        case 'notification.new':
          this.notifyListeners('message', data);
          break;
        
        case 'notification.count':
          this.notifyListeners('count', data);
          break;
        
        case 'heartbeat':
          // Heartbeat response - do nothing
          break;
        
        default:
          this.notifyListeners('message', data);
      }
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error);
    }
  }

  /**
   * Handle WebSocket error
   */
  handleError(event) {
    console.error('[WebSocket] Error:', event);
    this.notifyListeners('error', { error: event });
  }

  /**
   * Handle WebSocket close
   */
  handleClose(event) {
    console.log('[WebSocket] Connection closed:', event.code, event.reason);

    // Stop heartbeat
    this.stopHeartbeat();

    // Notify listeners
    this.notifyListeners('disconnected', {
      code: event.code,
      reason: event.reason,
    });

    // Attempt reconnect if not intentionally closed
    if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection
   */
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    setTimeout(() => {
      if (!this.isIntentionallyClosed && this.token) {
        this.connect(this.token);
      }
    }, delay);
  }

  /**
   * Start heartbeat ping
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ action: 'get_count' });
      }
    }, 30000); // 30 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Send message to WebSocket server
   * 
   * @param {Object} data - Message data
   */
  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
    }
  }

  /**
   * Mark notification as read
   * 
   * @param {string} notificationId - Notification UUID
   */
  markAsRead(notificationId) {
    this.send({
      action: 'mark_read',
      notification_id: notificationId,
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    console.log('[WebSocket] Disconnecting...');
    this.isIntentionallyClosed = true;
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.listeners.clear();
    this.token = null;
  }

  /**
   * Add event listener
   * 
   * @param {string} event - Event name ('message', 'connected', 'disconnected', 'error', 'count')
   * @param {Function} callback - Callback function
   * @returns {Function} Unsubscribe function
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }

    this.listeners.get(event).add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  /**
   * Notify all listeners for an event
   * 
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  notifyListeners(event, data) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach((callback) => callback(data));
    }
  }

  /**
   * Check if WebSocket is connected
   * 
   * @returns {boolean}
   */
  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();