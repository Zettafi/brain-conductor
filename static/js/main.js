import {ChatClient} from "./chat_client.js"
import {onChatMessageSent, onChatMessageResponseDelivered} from "./measurement.js";

const mediatorName = "Brain Conductor"
const chatBox = document.getElementById("chat_container");
const chatMembers = [];
const typingIndicator = document.getElementById('typing-indicator');
const connectIssueIndicator = document.getElementById('connection-issue-indicator');
// Main brain default message
let isScrollAtBottom = true;
const message = "Welcome to Brain Conductor.  I'm the Main Brain. " +
    "Ask any question, and it will be answered by an AI expert.\n\nSay hello " +
    "to a few of our experts!";
addBotMessage(mediatorName, message)
let modalIndex = 0

let userChatCount = 0; // Initialize user chat count

let wsURI;
if (window.location.protocol === "https:") {
    wsURI = "wss:";
} else {
    wsURI = "ws:";
}
wsURI += "//" + window.location.host + "/chat";

const client = new ChatClient(wsURI);

document.addEventListener("DOMContentLoaded", () => {
    function isChatBoxScrollAtBottom(container) {
        return container.scrollHeight - container.clientHeight <= container.scrollTop + 1;
    }

    chatBox.addEventListener("scroll", () => {
        isScrollAtBottom = isChatBoxScrollAtBottom(chatBox);
    })


});

function announceUserJoinedChat(from, greeting) {
    const chatJoinerText = document.createElement("div");
    chatJoinerText.className = "p-1 text-center text-gray mt-1";
    chatJoinerText.innerText = `${from} has entered the chat`;
    chatBox.appendChild(chatJoinerText);
    const expertMessage = document.createElement("div");
    expertMessage.className = "p-1 text-center text-blue";
    expertMessage.innerText = greeting;
    chatBox.appendChild(expertMessage);
}

/**
 * Add a bot message to the chat box
 * @param {string} from From whom the message originated
 * @param {string} text The message text
 * @param {string} [avatar] The URI of the avatar image
 * @param {[ChatDataItem]} [data=[]]
 */
function addBotMessage(from, text, avatar, data) {
    if (data === undefined) {
        data = [];
    }

    const botBubble = document.createElement("div");
    botBubble.className = "balloon2 p-2 m-0 position-relative";
    botBubble.setAttribute("data-is", `${from} - ${formattedTime()}`);
    const botMessage = document.createElement("a");
    botMessage.className = "float-left text-left";
    botMessage.innerHTML = text;
    // adding flex container for message and avatar
    const botMessageContainer = document.createElement("div");
    botMessageContainer.className = "d-flex flex-row bot-chat";
    const botAvatar = document.createElement("span");
    botAvatar.className = "ai-avatar";
    if (avatar) {
        botAvatar.style.backgroundImage = `url(${avatar})`;
    } else {
        botAvatar.style.backgroundImage = "url(/static/images/avatars/BrainIcon.png)";
        botAvatar.style.padding = "20px;"
    }
    botMessageContainer.appendChild(botAvatar);
    botMessageContainer.appendChild(botMessage);
    data.forEach((dataItem) => {
        if (dataItem.type === "image") {
            modalIndex += 1
            const modalId = `modal-${modalIndex}`;
            const image = $(`<img src="data:${dataItem.mimeType};${dataItem.encoding},${dataItem.content}" alt="${message}">`);
            $(botMessage).append(
                $(`<div id="${modalId}" class="modal fade" tabindex="-1" role="dialog">`)
                    .append($('<div class="modal-dialog  modal-dialog-centered" role="document">')
                        .append($('<div class="modal-content">')
                            .append(
                                $('<div>')
                                    .append(
                                        $(`<button type="button" class="close modal-close-btn" data-bs-dismiss="modal" data-bs2-target="#${modalId}" aria-label="Close">`)
                                            .append('<span aria-hidden="true">&times;</span>')
                                    ),
                                $('<div class="modal-body">')
                                    .append($('<div class="text-center">')
                                        .append(image.clone().addClass("img-fluid"))
                                    )
                            )
                        )
                    ),
                $(`<a data-modal="${modalId}" data-bs-toggle="modal" data-bs-target="#${modalId}">`)
                    .append(
                        $(image).addClass("img-thumbnail").attr("data-modal", modalId)
                    )
            );
        }
    });
    botBubble.appendChild(botMessageContainer);
    chatBox.appendChild(botBubble);
    if (isScrollAtBottom) {
        chatBox.lastElementChild.scrollIntoView();
    }

}

function addThinkingBubble() {
    //add thinking bubble
    const thinkingBotBubble = document.createElement("div");
    thinkingBotBubble.className = "thinking-bubble balloon2 p-2 m-0 position-relative";
    const botThinkingSpanContainer = document.createElement("div");
    botThinkingSpanContainer.className = "thinking-indicator"
    const spanItem1 = document.createElement("span");
    const spanItem2 = document.createElement("span");
    const spanItem3 = document.createElement("span");
    botThinkingSpanContainer.appendChild(spanItem1);
    botThinkingSpanContainer.appendChild(spanItem2);
    botThinkingSpanContainer.appendChild(spanItem3);

    // adding flex container for message and avatar
    const botMessageContainer = document.createElement("div");
    botMessageContainer.className = "d-flex flex-row bot-chat";
    const botAvatar = document.createElement("span");
    botAvatar.className = "ai-avatar";
    botAvatar.style.backgroundImage = "url(/static/images/avatars/BrainIcon.png)";
    botAvatar.style.padding = "20px;"

    botMessageContainer.appendChild(botAvatar);
    botMessageContainer.appendChild(botThinkingSpanContainer);
    thinkingBotBubble.appendChild(botMessageContainer);
    chatBox.appendChild(thinkingBotBubble);
    if (isScrollAtBottom) {
        chatBox.lastElementChild.scrollIntoView();
    }
}

function addUserMessage(message) {
    const userBubble = document.createElement("div");
    userBubble.className = "balloon1 p-2 m-0 position-relative";
    userBubble.setAttribute("data-is", `You - ${formattedTime()}`);

    // adding flex container for message and avatar
    const userMessageContainer = document.createElement("div");
    userMessageContainer.className = "d-flex flex-row-reverse user-chat";
    const userAvatar = document.createElement("span");
    userAvatar.className = "user-avatar";
    const userMessage = document.createElement("a");
    userMessage.className = "float-right";
    userMessage.innerText = message;
    userMessageContainer.appendChild(userMessage);
    userMessageContainer.appendChild(userAvatar);
    userBubble.appendChild(userMessageContainer);
    chatBox.appendChild(userBubble);
    chatBox.lastElementChild.scrollIntoView();
}

function send(event) {
    const message = (new FormData(event.target)).get("message");
    if (message) {
        // send message
        const id = client.sendMessage(message);
        onChatMessageSent(id);
        addUserMessage(message);
        addThinkingBubble();
        client.botMessageHistory.push({
            from: 'User',
            text: message,
        });
        userChatCount++; // Increment user chat count
    }
    event.target.reset();
    return false;
}

document.getElementById("chat-form").addEventListener("submit", send);

function formattedTime() {

    const d = new Date();
    let h = d.getHours(), m = d.getMinutes(), l = "AM";
    if (h > 12) {
        h = h - 12;
    }
    if (h < 10) {
        h = '0' + h;
    }
    if (m < 10) {
        m = '0' + m;
    }
    if (d.getHours() >= 12) {
        l = "PM"
    } else {
        l = "AM"
    }

    return h + ':' + m + ' ' + l;
}

client.onChatMessage = (id, from, text, avatar, data) => {
    $(typingIndicator).hide();
    $('.thinking-bubble.balloon2').remove();
    addBotMessage(from, text, avatar, data);
    onChatMessageResponseDelivered(id);
};

client.onPreparingResponse = (from, greeting) => {
    let timeout = 0;
    if (!chatMembers.includes(from)) {
        announceUserJoinedChat(from, greeting);
        chatMembers.push(from);
        timeout = 1000;
    }

    setTimeout(() => {
        document.getElementById('typing-indicator-text')
            .innerText = `${from} is typing a response`
        typingIndicator.style.visibility = "visible";
    }, timeout);
};

client.onSystemMessage = (id, message) => {
    addBotMessage(mediatorName, message);
    onChatMessageResponseDelivered(id);
};

client.onMembersListMessage = (botsList) => {
    if (chatMembers.length === 0) { // Don't do this on reconnect
        //show default message and ai experts
        botsList.forEach(expert => {
            chatMembers.push(expert.name);
            announceUserJoinedChat(expert.name, expert.greeting);
        });
    }
};

client.onDisconnected = () => {
    connectIssueIndicator.style.display = "block";
    document.getElementById("chat-message-input").setAttribute("disabled", "disabled");
    document.getElementById("chat-send-button").setAttribute("disabled", "disabled");
}

client.onConnected = () => {
    connectIssueIndicator.style.display = "none";
    document.getElementById("chat-message-input").removeAttribute("disabled");
    document.getElementById("chat-send-button").removeAttribute("disabled");
}

client.connect();

// Animate connection issue indicator image
(() => {
    const stages = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-wifi-1" viewBox="0 0 16 16">\n' +
        '  <path d="M11.046 10.454c.226-.226.185-.605-.1-.75A6.473 6.473 0 0 0 8 9c-1.06 0-2.062.254-2.946.704-.285.145-.326.524-.1.75l.015.015c.16.16.407.19.611.09A5.478 5.478 0 0 1 8 10c.868 0 1.69.201 2.42.56.203.1.45.07.611-.091l.015-.015zM9.06 12.44c.196-.196.198-.52-.04-.66A1.99 1.99 0 0 0 8 11.5a1.99 1.99 0 0 0-1.02.28c-.238.14-.236.464-.04.66l.706.706a.5.5 0 0 0 .707 0l.708-.707z"/>\n' +
        '</svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-wifi-2" viewBox="0 0 16 16">\n' +
        '  <path d="M13.229 8.271c.216-.216.194-.578-.063-.745A9.456 9.456 0 0 0 8 6c-1.905 0-3.68.56-5.166 1.526a.48.48 0 0 0-.063.745.525.525 0 0 0 .652.065A8.46 8.46 0 0 1 8 7a8.46 8.46 0 0 1 4.577 1.336c.205.132.48.108.652-.065zm-2.183 2.183c.226-.226.185-.605-.1-.75A6.473 6.473 0 0 0 8 9c-1.06 0-2.062.254-2.946.704-.285.145-.326.524-.1.75l.015.015c.16.16.408.19.611.09A5.478 5.478 0 0 1 8 10c.868 0 1.69.201 2.42.56.203.1.45.07.611-.091l.015-.015zM9.06 12.44c.196-.196.198-.52-.04-.66A1.99 1.99 0 0 0 8 11.5a1.99 1.99 0 0 0-1.02.28c-.238.14-.236.464-.04.66l.706.706a.5.5 0 0 0 .708 0l.707-.707z"/>\n' +
        '</svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-wifi" viewBox="0 0 16 16">\n' +
        '  <path d="M15.384 6.115a.485.485 0 0 0-.047-.736A12.444 12.444 0 0 0 8 3C5.259 3 2.723 3.882.663 5.379a.485.485 0 0 0-.048.736.518.518 0 0 0 .668.05A11.448 11.448 0 0 1 8 4c2.507 0 4.827.802 6.716 2.164.205.148.49.13.668-.049z"/>\n' +
        '  <path d="M13.229 8.271a.482.482 0 0 0-.063-.745A9.455 9.455 0 0 0 8 6c-1.905 0-3.68.56-5.166 1.526a.48.48 0 0 0-.063.745.525.525 0 0 0 .652.065A8.46 8.46 0 0 1 8 7a8.46 8.46 0 0 1 4.576 1.336c.206.132.48.108.653-.065zm-2.183 2.183c.226-.226.185-.605-.1-.75A6.473 6.473 0 0 0 8 9c-1.06 0-2.062.254-2.946.704-.285.145-.326.524-.1.75l.015.015c.16.16.407.19.611.09A5.478 5.478 0 0 1 8 10c.868 0 1.69.201 2.42.56.203.1.45.07.61-.091l.016-.015zM9.06 12.44c.196-.196.198-.52-.04-.66A1.99 1.99 0 0 0 8 11.5a1.99 1.99 0 0 0-1.02.28c-.238.14-.236.464-.04.66l.706.706a.5.5 0 0 0 .707 0l.707-.707z"/>\n' +
        '</svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-wifi-2" viewBox="0 0 16 16">\n' +
        '  <path d="M13.229 8.271c.216-.216.194-.578-.063-.745A9.456 9.456 0 0 0 8 6c-1.905 0-3.68.56-5.166 1.526a.48.48 0 0 0-.063.745.525.525 0 0 0 .652.065A8.46 8.46 0 0 1 8 7a8.46 8.46 0 0 1 4.577 1.336c.205.132.48.108.652-.065zm-2.183 2.183c.226-.226.185-.605-.1-.75A6.473 6.473 0 0 0 8 9c-1.06 0-2.062.254-2.946.704-.285.145-.326.524-.1.75l.015.015c.16.16.408.19.611.09A5.478 5.478 0 0 1 8 10c.868 0 1.69.201 2.42.56.203.1.45.07.611-.091l.015-.015zM9.06 12.44c.196-.196.198-.52-.04-.66A1.99 1.99 0 0 0 8 11.5a1.99 1.99 0 0 0-1.02.28c-.238.14-.236.464-.04.66l.706.706a.5.5 0 0 0 .708 0l.707-.707z"/>\n' +
        '</svg>'
    ]
    const icon = document.getElementById("connection-issue-indicator-image");
    const interval = 400;
    let index = 0;

    const swap = () => {
        icon.innerHTML = stages[index];
        index += 1;
        if (index >= stages.length) {
            index = 0;
        }
        setTimeout(swap, interval);
    }
    swap();
})();

//Alert msgs
function createAlert(title, summary, details, severity, dismissible, autoDismiss, appendToId) {
    var iconMap = {
        info: "fa fa-info-circle",
        success: "fa fa-thumbs-up",
        warning: "fa fa-exclamation-triangle",
        danger: "fa ffa fa-exclamation-circle"
    };

    var iconAdded = false;

    var alertClasses = ["alert", "animated", "flipInX"];
    alertClasses.push("alert-" + severity.toLowerCase());

    if (dismissible) {
    alertClasses.push("alert-dismissible");
    }

    var msgIcon = $("<i />", {
        "class": iconMap[severity] // you need to quote "class" since it's a reserved keyword
    });

    var msg = $("<div />", {
        "class": alertClasses.join(" ") // you need to quote "class" since it's a reserved keyword
    });

    if (title) {
        var msgTitle = $("<h4 />", {
            html: title
        }).appendTo(msg);

        if(!iconAdded){
            msgTitle.prepend(msgIcon);
            iconAdded = true;
        }
    }

    if (summary) {
        var msgSummary = $("<strong />", {
            html: summary
        }).appendTo(msg);

        if(!iconAdded){
            msgSummary.prepend(msgIcon);
            iconAdded = true;
        }
    }

    if (details) {
        var msgDetails = $("<p />", {
            html: details
        }).appendTo(msg);

        if(!iconAdded){
            msgDetails.prepend(msgIcon);
            iconAdded = true;
        }
    }


    if (dismissible) {
        var msgClose = $("<span />", {
            "class": "close", // you need to quote "class" since it's a reserved keyword
            "data-bs-dismiss": "alert",
            html: "<i class='fa fa-times-circle'></i>"
        }).appendTo(msg);
    }

    $('#' + appendToId).prepend(msg);

    if(autoDismiss){
        setTimeout(function(){
            msg.addClass("flipOutX");
            setTimeout(function(){
            msg.remove();
            },1000);
        }, 3000);
    }
}