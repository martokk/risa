/**
 * LogStreamer provides functionality to stream logs into a Bootstrap modal
 * via a WebSocket connection.
 */
export class LogStreamer {
    /**
     * @param {string} modalId - The ID of the Bootstrap modal element for displaying logs.
     * @param {string} logContentId - The ID of the element inside the modal where log content will be written.
     * @param {string} scrollToBottomBtnId - The ID of the button to scroll to the bottom of the log.
     * @param {WebSocket} webSocket - The WebSocket instance to use for communication.
     */
    constructor(modalId, logContentId, scrollToBottomBtnId, webSocket) {
        this.modalEl = document.getElementById(modalId);
        this.logContentEl = document.getElementById(logContentId);
        this.scrollToBottomBtn = document.getElementById(scrollToBottomBtnId);

        if (!this.modalEl || !this.logContentEl || !this.scrollToBottomBtn) {
            throw new Error("One or more required log streamer elements are not found in the DOM.");
        }

        this.modal = new bootstrap.Modal(this.modalEl);
        this.webSocket = webSocket;
        this.currentLogId = null; // e.g., job_id

        this._setupEventListeners();
    }

    _setupEventListeners() {
        // Show/hide the scroll-to-bottom button
        this.logContentEl.addEventListener('scroll', () => {
            if (this._isScrolledToBottom()) {
                this.scrollToBottomBtn.style.display = 'none';
            } else {
                this.scrollToBottomBtn.style.display = 'block';
            }
        });

        // Scroll to bottom button click
        this.scrollToBottomBtn.addEventListener('click', () => {
            this._scrollToBottom();
            this.scrollToBottomBtn.style.display = 'none';
        });

        // Clean up when modal is closed
        this.modalEl.addEventListener('hidden.bs.modal', () => {
            this.currentLogId = null;
            this.logContentEl.textContent = '';
            this.scrollToBottomBtn.style.display = 'none';
        });

        // Auto-scroll when modal is shown
        this.modalEl.addEventListener('shown.bs.modal', () => {
            this._scrollToBottom();
            this.scrollToBottomBtn.style.display = 'none';
        });

        // Handle incoming WebSocket messages
        this.webSocket.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'log_update' && data.job_id === this.currentLogId) {
                    this._appendLog(data.content);
                } else if (data.type === 'log_error' && data.job_id === this.currentLogId) {
                    this._appendLog(`\n[Error streaming log: ${data.error}]`, true);
                }
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        });
    }

    _isScrolledToBottom() {
        // Check if the element is scrolled to the bottom (with a 10px tolerance)
        return this.logContentEl.scrollHeight - this.logContentEl.scrollTop - this.logContentEl.clientHeight < 10;
    }

    _scrollToBottom() {
        this.logContentEl.scrollTop = this.logContentEl.scrollHeight;
    }

    _appendLog(content, isError = false) {
        const wasAtBottom = this._isScrolledToBottom();
        this.logContentEl.textContent += content;
        if (wasAtBottom) {
            this._scrollToBottom();
        }
    }

    /**
     * View a log by its ID.
     * @param {string} logId - The ID of the log to view (e.g., job ID).
     * @param {string} logType - The type of log ('job' or 'consumer').
     */
    viewLog(logId, logType = 'job') {
        this.logContentEl.textContent = 'Loading...';
        this.modal.show();
        this.currentLogId = logId;

        const message = {
            type: logType === 'job' ? 'subscribe_log' : `subscribe_${logType}_log`,
        };

        if (logType === 'job') {
            message.job_id = logId;
        }

        if (this.webSocket && this.webSocket.readyState === WebSocket.OPEN) {
            this.logContentEl.textContent = '';
            this.webSocket.send(JSON.stringify(message));
        } else {
            // If socket is not ready, wait and retry.
            const interval = setInterval(() => {
                if (this.webSocket && this.webSocket.readyState === WebSocket.OPEN) {
                    clearInterval(interval);
                    this.logContentEl.textContent = '';
                    this.webSocket.send(JSON.stringify(message));
                }
            }, 200);
        }
    }
} 
