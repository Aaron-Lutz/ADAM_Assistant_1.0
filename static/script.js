/* document.addEventListener('DOMContentLoaded', function() {
    playAudio('/get_intro_audio');
}, false);
*/

function convertUrlsToLinks(text) {
    return text.replace(/(https?:\/\/[^\s\)]+)/g, function(match) {
        let displayText = match;
        if (match.length > 30) { // Truncate links longer than 30 characters
            displayText = match.substring(0, 27) + '...';
        }
        return '<a href="' + match + '" target="_blank">' + displayText + '</a>';
    });
}

function setInputValue(value) {
    var userInput = document.getElementById("user-input");
    userInput.value = value;
    userInput.focus();
}

function sendCommand() {
    stopAudio();
    var prompt = document.getElementById("user-input").value;

    // Add the user's command to the chat history
    var userBubble = document.createElement("div");
    userBubble.className = "user_bubble";
    userBubble.textContent = prompt;
    var chatHistoryInner = document.getElementById("chat-history-inner");
    chatHistoryInner.appendChild(userBubble);

    // Scroll to the bottom of the chat history
    chatHistoryInner.scrollTop = chatHistoryInner.scrollHeight;
    
    document.getElementById("user-input").value = '';
    document.getElementById("example-prompts-container").style.display = 'none';
    document.getElementById("welcomemessage").style.display = 'none';
    resizeTextarea(userInput);

    // Add a typing animation bubble
    var typingBubble = document.createElement("div");
    typingBubble.className = "typing_bubble";
    typingBubble.innerHTML = "<span></span><span></span><span></span>"; // Three dots for typing animation
    chatHistoryInner.appendChild(typingBubble);
    // Scroll to the bottom of the chat history
    chatHistoryInner.scrollTop = chatHistoryInner.scrollHeight;

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/process_command", true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var json = JSON.parse(xhr.responseText);  // Parse the server response
    
            // Remove the typing bubble
            typingBubble.remove();
    
            // Add the assistant's response to the chat history
            var aiBubble = document.createElement("div");
            aiBubble.className = "ai_bubble";
            aiBubble.innerHTML = convertUrlsToLinks(json.response);
            chatHistoryInner.appendChild(aiBubble);
            
            // Scroll to the bottom of the chat history
            chatHistoryInner.scrollTop = chatHistoryInner.scrollHeight;
    
            // Play the assistant's response
            playAudio('/get_audio');
        }
    };

    // Get coordinates and send the data
    getCoordinates(function(lat, long) {
        var data = JSON.stringify({
            "prompt": prompt,
            "latitude": lat,
            "longitude": long
        });
        xhr.send(data);
    });
}

function getCoordinates(callback) {
    navigator.geolocation.getCurrentPosition(function(position) {
        let lat = position.coords.latitude;
        let long = position.coords.longitude;
        callback(lat, long);
    });
}


// Flag to indicate if recognition is currently active
let isListening = false;
// Flag to indicate if recognition was stopped manually
let manuallyStopped = false;

// Function to detect if the user is on a mobile device
function isMobileDevice() {
    return (typeof window.orientation !== "undefined") || (navigator.userAgent.indexOf('IEMobile') !== -1);
}

document.getElementById("user-input").addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        var userInput = document.getElementById("user-input").value;
        
        if (userInput === "") {
            if (isMobileDevice()) {
                toggleRecognition();
            } else {
                isListening = false;  // Reset the flag for desktop
                recognition.start();
            }
        } else {
            stopAudio();  // I'm assuming this function is defined elsewhere in your code
            sendCommand();  // I'm assuming this function is defined elsewhere in your code
        }
    }
});

// Speech to text
var recognition = new webkitSpeechRecognition();
recognition.continuous = false;

recognition.onstart = function() {
    console.log('Recognition started');
    document.getElementById('mic-icon').src = '../static/img/mic-icon-red.jpg'; 
    isListening = true;  // Update the flag
}

recognition.onresult = function(event) {
    console.log('Recognition result received');
    var transcript = event.results[0][0].transcript;
    console.log('Transcript:', transcript);
    document.getElementById('user-input').value = transcript;
    sendCommand();  // I'm assuming this function is defined elsewhere in your code
}

recognition.onend = function() {
    console.log('Recognition ended');
    if (!manuallyStopped) {
        document.getElementById('mic-icon').src = '../static/img/mic-icon.png';
        isListening = false;  // Update the flag
    }
    // Reset the manuallyStopped flag regardless
    manuallyStopped = false;
}

document.getElementById('speak').onclick = function() {
    console.log('Mic button clicked');
    toggleRecognition();
}

function toggleRecognition() {
    if (isListening) {
        manuallyStopped = true;  // Set this flag when manually stopping
        recognition.stop();
        isListening = false;  // Update the flag when stopping
    } else {
        manuallyStopped = false;
        recognition.start();
        isListening = true;   // Update the flag when starting
    }
}



//remove url from text
function removeUrls(text) {
    // Remove URLs
    text = text.replace(/https?:\/\/[^\s]+|www\.[^\s]+/g, '');
}

document.getElementById("reset-button").addEventListener("click", resetChat);

function resetChat() {
    stopAudio();    
    // Clear the chat history in the frontend
    var chatHistoryInner = document.getElementById("chat-history-inner");
    chatHistoryInner.innerHTML = "";

    var aiBubble = document.createElement("div");
    aiBubble.className = "ai_bubble";
    aiBubble.innerHTML = '<p id="message">Hello, I am A.D.A.M., your automated digital assistant mainframe! I am here to help you with your tasks and answer all your questions. This is an alpha version. Currently, I am capable of performing web searches, giving weather updates and managing your calendar, emails, and tasks. <a href="https://booming-oarlock-205714.oa.r.appspot.com/login">Login with your Google Account</a> to grant me access to automate your every day life.</p>';

    var chatHistoryInner = document.getElementById("chat-history-inner");
    chatHistoryInner.appendChild(aiBubble);

    // Send a request to the server to clear the chat history
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/reset_chat", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify({}));
}

var audioContext = new (window.AudioContext || window.webkitAudioContext)();
var source;

var audioContext = new (window.AudioContext || window.webkitAudioContext)();
var source;

//play TTS audio
function playAudio(url) {
    if (source) {
        source.stop();
    }

    // Create an AudioBufferSourceNode
    source = audioContext.createBufferSource();

    // Create an AnalyserNode
    var analyser = audioContext.createAnalyser();

    // Fetch the audio file
    fetch(url)
    .then(response => response.arrayBuffer())
    .then(arrayBuffer => audioContext.decodeAudioData(arrayBuffer))
    .then(audioBuffer => {
        source.buffer = audioBuffer;
        source.connect(analyser);
        analyser.connect(audioContext.destination);
        source.start(0);
    });

    // Use the frequency data from the AnalyserNode to animate the assistant
    var assistantImage = document.getElementById("assistant-image");
    var frequencyData = new Uint8Array(analyser.frequencyBinCount);
    function animate() {
        requestAnimationFrame(animate);
        analyser.getByteFrequencyData(frequencyData);

        // Calculate the volume as a percentage
        var volume = Math.max(...frequencyData) / 255;

        // Use the volume to animate the assistant
        assistantImage.style.transform = `scale(${1 + volume * 0.15})`;
    }

    animate();
}

// Stop TTS playback
function stopAudio() {
    // If there's an existing source, stop it
    if (source) {
        source.stop();
    }
}

function resizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

let userInput = document.getElementById('user-input');
userInput.addEventListener('input', function () {
    resizeTextarea(this);
});






