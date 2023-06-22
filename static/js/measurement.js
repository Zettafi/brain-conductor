const messagesAwaitingResponse = [];

/**
 *
 * @param {string} event_name Name of the event to send
 * @param {object} [event_parameters] A collection of parameters that provide additional
 * information about the event
 */
function triggerEvent(event_name, event_parameters) {
    if (typeof gtag !== "undefined") {
        gtag("event", event_name, event_parameters);
    }
}

/**
 * This function should be called AFTER any message response has been delivered
 * to the user.
 * @param {String} id Unique identifier of the message which had received the response
 */
export function onChatMessageResponseDelivered(id) {
    const index = messagesAwaitingResponse.indexOf(id);
    if (index >= 0) {
        messagesAwaitingResponse.splice(index, 1);
        let responses;
        const key = "measurement.chat.initial_responses.received";
        let responsesItem = localStorage.getItem(key);
        if (responsesItem === null) {
            responses = 0;
        } else {
            responses = Number.parseInt(responsesItem);
        }
        responses += 1;
        localStorage.setItem(key, responses)
        triggerEvent(`ReceivedChatInitialResponse${responses}`)
        triggerEvent(`ReceivedChatResponse`)
    }
}

/**
 * This function should be called after sending a chat message
 * @param {String} id Unique identifier of the message which was sent
 */
export function onChatMessageSent(id) {
    messagesAwaitingResponse.push(id);
    const key = "measurement.chat.requests.sent";
    let requests;
    let requestsItem = localStorage.getItem(key);
    if (requestsItem === null) {
        requests = 0;
    } else {
        requests = Number.parseInt(requestsItem);
    }
    requests += 1;
    localStorage.setItem(key, requests)
    triggerEvent(`SentChatMessage${requests}`)
    triggerEvent(`SentChatMessage`)
}