/**
 * Client for connecting and conversing with the chat server.
 *
 * Chat messages are sent via {@see sendMessage}.
 * Messages from the chat server are asynchronous and can be
 * processed by overriding the event handler methods:
 *
 * {@see onChatMessage}: Receiving a chat message
 * {@see onMembersListMessage}; Receiving this list of chat members
 * {@see onSystemMessage}: Receiving a message from the chat server
 * {@see onEchoMessage}: Receiving the message sent via {@see sendMessage}
 * as received by the chat server.
 */
class ChatDataItem {
    constructor(content, type, encoding, mimeType) {
        this.content = content;
        this.type = type;
        this.encoding = encoding;
        this.mimeType = mimeType;
    }
}

class ChatClient {
    /**
     * Full websocket URI to connect to the chat server
     * @param {string} wsURI Websocket URI
     */
    constructor(wsURI) {
        this.uri = wsURI
        this.connectBackoffLevel = 0;
        this.botMessageHistory = []
        this.messageQueue = []
        this.unrespondedInquiryIds = []
        this.messageID = 0;
    }

    /**
     * Connect to the server
     */
    connect() {
        let connecting = true;
        this.websocket = new WebSocket(this.uri);
        this.websocket.addEventListener("message", this.onMessage.bind(this));
        this.websocket.addEventListener("open", this.connectedHandler.bind(this));
        this.websocket.addEventListener("error", this.connectionErrorHandler.bind(this));
    }

    /**
     * Handler for websocket connected events
     * @private
     */
    connectedHandler() {
        this.connectBackoffLevel = 0;
        this.processMessageQueue();
        this.onConnected();
    }

    /**
     * Handler for websocket connection errors
     * @private
     */
    connectionErrorHandler() {
        if (this.websocket.readyState === this.websocket.CLOSED) {
            // Determine max wait time based on exponential backoff and 10K limit
            let maxWaitMS = 100 * Math.pow(2, this.connectBackoffLevel);
            if (maxWaitMS > 10000) {
                maxWaitMS = 10000;
            }
            // Get actual wait time with full jitter to reduce client contention
            // @see https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
            const waitMS = Math.floor(Math.random() * maxWaitMS);
            this.connectBackoffLevel += 1;
            console.log(`Error connecting. Retrying after ${waitMS} milliseconds`);
            setTimeout(this.connect.bind(this), waitMS);
        }
    }

    /**
     * Send a chat message from the site user
     * @param message
     * @return {string} Unique message identifier
     */
    sendMessage(message) {
        const messageID = this.messageID++;
        const socketMessage = JSON.stringify({
            id: messageID,
            type: "inquiry",
            text: message
        });
        // noinspection FallThroughInSwitchStatementJS
        switch (this.websocket.readyState) {
            case this.websocket.OPEN:
                this.websocket.send(socketMessage);
                break;
            case this.websocket.CLOSING:
            case this.websocket.CLOSED:
                console.log("Websocket is not open. Reconnecting...");
                this.connect();
            case this.websocket.CONNECTING:
                this.messageQueue.push(this.getReconnectMessage());
                this.messageQueue.push(socketMessage);
                this.onDisconnected();
                break;
        }
        return messageID;
    }

    /**
     * Process all messages in the {@link messageQueue} in
     * First In First Out (FIFO) order
     * @private
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.websocket.send(message);
        }
    }

    /**
     * Event handler for receiving websocket messages
     * @param event Websocket message event
     * @private
     */
    onMessage(event) {
        const message = JSON.parse(event.data);
        switch (message.type) {
            case "bot-message":
                this.botMessageHistory.push({
                    from: message.from,
                    text: message.text,
                });
                const chatData = message.data.map((item) => {
                    return new ChatDataItem(
                        item.content,
                        item.type,
                        item.encoding,
                        item.mimeType
                    )
                });
                this.onChatMessage(
                    message.id,
                    message.from,
                    message.text,
                    message.avatar,
                    chatData
                );
                break;
            case "system-message":
                this.onSystemMessage(message.id, message.text);
                break;
            case "experts-list":
                this.onMembersListMessage(message.experts);
                break;
            case "preparing-response":
                this.onPreparingResponse(message.from, message.greeting);
                break;
            case "error":
                console.log(message.id, message.text)
        }
    }

    /**
     * Get the message to send the websocket when a reconnect occurs
     * @returns {string} Reconnect message
     * @private
     */
    getReconnectMessage() {
        const reconnectHistory = this.botMessageHistory.map((item) => {
            return {
                from: item.from,
                text: item.text,
            }
        });
        return JSON.stringify({
            type: "reconnect",
            history: reconnectHistory
        });
    }

    /**
     * Function called when a message is received from one of the bots
     * @param {string} id Unique identifier for the original inquiry message
     * @param {string} from Bot from which the message was sent
     * @param {string} text Message text
     * @param {string} avatar URI of the boot's avatar
     * @param {[ChatDataItem]} data Data associated with the message
     * @interface
     */
    onChatMessage(id, from, text, avatar, data) {
    }

    /**
     * Function called when a system message is received.
     * @param {string} id Unique identifier for message
     * @param {string} message Message text
     * @interface
     */
    onSystemMessage(id, message) {
    }

    /**
     * List of experts that will communicate
     * @param {Object[]} bots List of bots in the system
     * @param {string} bots[].name Name of the bot
     * @param {string} bots[].greeting Introductory greeting for the bot
     * @interface
     */
    onMembersListMessage(bots) {
    }

    /**
     * Function called when connection with the chat server is lost
     */
    onDisconnected() {
    }

    /**
     * Function called when connection with the chat server is restored
     */
    onConnected() {
    }

    /**
     *
     * Function called when a bot is preparing a response
     * @param {string} from The bot preparing a message
     * @param {string} greeting The initial greeting from the bot preparing a message
     * */
    onPreparingResponse(from, greeting) {
    }
}

export {ChatClient, ChatDataItem};
