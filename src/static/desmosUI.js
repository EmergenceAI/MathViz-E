
const origin = window.origin;

let speechRecognition;
let speechInputOngoing = false;
let messageTosend = "";
let showingExplanation = true;
let userMessage;

//Preload in and out chimes to reduce network latency during runtime
let inChime = new Audio('static/inchime.mp3');
inChime.load();

let outChime = new Audio('static/outchime.mp3');
outChime.load();

window.addEventListener("DOMContentLoaded", (event) => {
    userMessage = document.getElementById('user-message');
    userMessage.addEventListener('focus', () => {
        if (userMessage.textContent.trim() === userMessage.getAttribute('placeholder')) {
            userMessage.innerHTML = '&nbsp;';
            userMessage.style.border = '1px solid purple';
            userMessage.style.color = 'rgba(0, 0, 0, 1)';
        }
    });
    userMessage.addEventListener('blur', () => {
        if (userMessage.textContent.trim() === '' || userMessage.innerHTML === '&nbsp;') {
            let placeholder = userMessage.getAttribute('placeholder');
            userMessage.textContent = placeholder;
            userMessage.style.color = 'rgba(0, 0, 0, 0.6)';
            userMessage.style.border = '1px solid gray';
            console.log("Input field lost focus, Finished setting placeholder");
        }
    });
    
    if (userMessage.textContent.trim() === '') {
        userMessage.textContent = userMessage.getAttribute('placeholder');
        userMessage.style.color = 'rgba(0, 0, 0, 0.6)';
        userMessage.style.border = '1px solid gray';
    }
    userMessage.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default behavior (newline)
            const messageTosend = userMessage.innerText.trim();
            if (messageTosend !== '' && messageTosend !== userMessage.getAttribute('placeholder')) {
                userMessage.textContent='';
                userMessage.innerText='';
                userMessage.blur();
                userMessage.dispatchEvent(new FocusEvent('blur'));
                let id = sendUserMessage(messageTosend);
            }
        }
    });
    let overlay_icon = document.getElementById('overlay-icon');
    showExplanationPanel();

    overlay_icon.addEventListener('click', () => {
        if (showingExplanation) {
            hideExplanationPanel();
            showingExplanation=false;
        }
        else {
            showExplanationPanel();
            showingExplanation=true;
        }
    });

    let clear_button=document.getElementById('clear-chat');
    clear_button.addEventListener('click', ()=>{
        clearMessages();
        clearDesmos();
    });
    if (!('webkitSpeechRecognition' in window)) {
        alert("Speech API is not supproted. Try on chromium based browsers (e.g. Google chrome) ");
    }
    else {
        speechRecognition = new webkitSpeechRecognition();
        console.log("Speech API initialised");   
        speechRecognition.continuous = true;
        speechRecognition.interimResults = true;
        speechRecognition.lang = "en-US";

        speechRecognition.onstart = function () {
            console.log("Speech recognition started");
            speechInputOngoing=true;
        }
        speechRecognition.onend = function () {
            console.log("Speech recognition ended");
            speechInputOngoing = false;
        }    
    }

    window.addEventListener('keydown', (event) => {
        var final_transcript = "";
        if (userMessage === document.activeElement) {
            return;
        }
    
        if (event.key == 'M' || event.key == 'm') {

            if (speechInputOngoing == false) {
                console.log("M Key down, activating speech recognition");
                if (!speechRecognition.listening) {
                    speechRecognition.start();
                }
                try {
                    inChime.play()
                } catch (error) {
                }

                userMessage.classList.remove('default');
                userMessage.classList.add('highlight');
                messageTosend = "";
                speechRecognition.onresult = function (event) {
                    let interim_transcript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            final_transcript += event.results[i][0].transcript;
                            const elem = document.getElementById("user-message");
                            elem.innerHTML = final_transcript;
                            messageTosend = final_transcript;

                        } else {
                            interim_transcript += event.results[i][0].transcript;
                            const elem = document.getElementById("user-message");
                            elem.innerHTML = final_transcript+ " "+ interim_transcript;
                            console.log("Interim : " + interim_transcript);
                        }
                    }
                };
            }
        }
    
        if (event.key === "Escape") {
            if (showingExplanation) {
                hideExplanationPanel();
                showingExplanation=false;
            }
            else {
                showExplanationPanel();
                showingExplanation=true;
            }
        }
    });
});


window.addEventListener('keyup', (event) => {
    if (event.key == 'M' || event.key == 'm') {
        if (speechInputOngoing) {
            try {
                outChime.play()
            } catch (error) {

            }
            userMessage.classList.remove('highlight');
            userMessage.classList.add('default');
            speechRecognition.stop();
   
            setTimeout(function () {
                userMessage.innerHTML="";
                userMessage.blur();
                userMessage.dispatchEvent(new FocusEvent('blur'));
                if (messageTosend.trim()!="") {
                    let id = sendUserMessage(messageTosend);
                    console.log("Sending to server from M key up " + messageTosend);
                    messageTosend = "";
                }

            }, 100);
        }
    }

});

//useful if we want to support multiple simultaneous sessions
let sessionID = generateID();

function generateID() {
    return Math.random().toString(36).substr(2, 5);
}

function sendUserMessage(messageTosend) {
    showExplanationPanel();
    showingExplanation=true;
    addMessage(messageTosend, "user");
    expressions = getExpressions();
    interpretUtterance(sessionID, messageTosend, expressions);
}


function showExplanationPanel(){
    if(!showingExplanation){
        let panel=document.getElementById('chat-debug-overlay');
        panel.classList.add('show');
        panel.classList.remove('hide');
    
        let overlayicon=document.getElementById('overlay-icon');
        overlayicon.classList.add('expanded');
        overlayicon.classList.remove('collapsed');
    }
}

function updateExplanationPanel(agent, content){
    addMessage(content, agent.toLowerCase());
}

function hideExplanationPanel(){
    if(showingExplanation){
        let panel=document.getElementById('chat-debug-overlay');
        panel.classList.add('hide');
        panel.classList.remove('show');
        let overlayicon=document.getElementById('overlay-icon');
        overlayicon.classList.add('collapsed');
        overlayicon.classList.remove('expanded');
    }
}


function addMessage(message, sender) {
    //console.log(`Adding ${sender} message: ${message}`);
    let newDiv = document.createElement("div");
    newDiv.classList.add("chat-input");
  
    let iconDiv1 = document.createElement("div");
    iconDiv1.classList.add("icon");
  
    let chatDiv = document.createElement("div");
    chatDiv.classList.add("chat");
  
    let iconDiv2 = document.createElement("div");
    iconDiv2.classList.add("icon");
  
    newDiv.appendChild(iconDiv1);
    newDiv.appendChild(chatDiv);
    newDiv.appendChild(iconDiv2);
    let parsedMessage = message;

    // Customize based on the sender
    if (sender === "user") {
      iconDiv2.classList.add("user");
      chatDiv.classList.add("chattext");
      chatDiv.classList.add("chat-right-align");
      chatDiv.textContent = parsedMessage;
    }
    else if (sender === "wolfram") {
        iconDiv1.classList.add("agent1");
        chatDiv.classList.add("chattext");
        chatDiv.classList.add("chat-left-align");
        chatDiv.textContent = parsedMessage;
    } 
    else if(sender === "math viz"){
        iconDiv1.classList.add("agent2");
        chatDiv.classList.add("chattext");
        chatDiv.classList.add("chat-left-align");
        chatDiv.textContent = parsedMessage;
    }
    else{
        iconDiv1.classList.add("agent3");
        chatDiv.classList.add("chattext");
        chatDiv.classList.add("chat-left-align");
        chatDiv.textContent = parsedMessage;
    }
  
    let chatBox = document.getElementById('chat-box');
    chatBox.appendChild(newDiv);
    // Check if chatBox is overflowing
    if (chatBox.scrollHeight > chatBox.clientHeight) {
        // Scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }
  }
  

function clearMessages(){
    let chatBox = document.getElementById('chat-box');
    chatBox.innerHTML="";
}