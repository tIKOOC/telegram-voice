// client/app.js - Complete Frontend Integration

// ===== CONFIGURATION =====
const SERVER = "http://localhost:8000"; // 🔧 Thay URL server của bạn. Khi deploy, hãy thay bằng URL của server thật.
const PORCUPINE_KEY = import.meta.env.VITE_PORCUPINE_KEY;
const HF_TOKEN = import.meta.env.VITE_HF_TOKEN;

// ===== DOM ELEMENTS =====
const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const transcriptEl = document.getElementById("transcriptText");

// ===== GLOBAL STATE =====
let recentMsgs = [];  // [{idx, chat_id, sender, text}]
let nextIdx = 1;      // Auto-incrementing index
let ws = null;        // WebSocket connection
let mediaRecorder, audioChunks = [];
let audioContext, analyser, micSource, silenceTimer;

// ===== UTILITY FUNCTIONS =====
function log(message) { 
  const timestamp = new Date().toLocaleTimeString();
  const logMessage = `[${timestamp}] ${message}`;
  console.log(logMessage); 
  if (logEl) {
    logEl.textContent += logMessage + "\n";
    logEl.scrollTop = logEl.scrollHeight;
  }
}

function updateStatus(message, type = "info") {
  if (statusEl) {
    statusEl.textContent = message;
    statusEl.className = `status-${type}`;
  }
  log(`Status: ${message}`);
}

function speakFeedback(text) {
  console.log("🔊 Speaking:", text);
  try {
    const synth = window.speechSynthesis;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "vi-VN";
    utter.rate = 0.9;
    utter.pitch = 1.0;
    synth.speak(utter);
  } catch (error) {
    console.error("Speech synthesis error:", error);
  }
}

// ===== MESSAGE MANAGEMENT =====
function addMessage(chat_id, sender, text) {
  // Add to recent messages with auto-increment index
  const newMessage = {
    idx: nextIdx++,
    chat_id: parseInt(chat_id),
    sender: sender,
    text: text,
    timestamp: new Date()
  };
  
  recentMsgs.unshift(newMessage);
  
  // Keep only last 20 messages
  if (recentMsgs.length > 20) {
    recentMsgs.pop();
  }
  
  // Add to inbox display
  displayMessage(newMessage);
  
  // Voice feedback
  speakFeedback(`Tin số ${newMessage.idx} từ ${sender}.`);
  
  log(`📨 New message #${newMessage.idx} from ${sender}: ${text.substring(0, 50)}...`);
}

function displayMessage(message) {
  let inboxEl = document.getElementById("inbox");
  
  // Create inbox if doesn't exist
  if (!inboxEl) {
    inboxEl = document.createElement("div");
    inboxEl.id = "inbox";
    inboxEl.innerHTML = "<h3>📨 Tin Nhắn Gần Đây:</h3>";
    inboxEl.style.cssText = `
      margin: 20px 0; 
      padding: 16px; 
      background: #fff; 
      border-radius: 8px; 
      border: 1px solid #e8ecef;
      max-height: 400px;
      overflow-y: auto;
    `;
    document.querySelector('.main').appendChild(inboxEl);
  }
  
  // Create message element
  const messageDiv = document.createElement("div");
  messageDiv.style.cssText = `
    margin: 8px 0; 
    padding: 12px; 
    background: #f8f9fa; 
    border-radius: 6px;
    border-left: 4px solid #007bff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  `;
  
  messageDiv.innerHTML = `
    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
      <strong style="color: #007bff;">#${message.idx} | ${message.sender}</strong>
      <small style="color: #6c757d;">${message.timestamp.toLocaleTimeString()}</small>
    </div>
    <div style="color: #495057;">${message.text}</div>
    <small style="color: #6c757d; font-size: 0.8em;">Chat ID: ${message.chat_id}</small>
  `;
  
  // Insert at top (after header)
  const header = inboxEl.querySelector('h3');
  if (header && header.nextSibling) {
    inboxEl.insertBefore(messageDiv, header.nextSibling);
  } else {
    inboxEl.appendChild(messageDiv);
  }
  
  // Keep only 20 visual messages
  const messages = inboxEl.querySelectorAll('div[style*="border-left"]');
  if (messages.length > 20) {
    messages[messages.length - 1].remove();
  }
}

// ===== WEBSOCKET MANAGEMENT =====
function connectWebSocket() {
  const wsUrl = SERVER.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws';
  
  log(`🔌 Connecting to WebSocket: ${wsUrl}`);
  ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    log("✅ WebSocket connected successfully");
    updateStatus("Connected - Say 'Hey Viso'", "success");
    
    // Send heartbeat every 30 seconds
    setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "heartbeat" }));
      }
    }, 30000);
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (error) {
      console.error("WebSocket message parse error:", error);
      log(`❌ Failed to parse WebSocket message: ${event.data}`);
    }
  };
  
  ws.onclose = (event) => {
    log(`🔌 WebSocket disconnected: ${event.code} - ${event.reason}`);
    updateStatus("Disconnected - Reconnecting...", "warning");
    
    // Reconnect after 3 seconds
    setTimeout(() => {
      if (!ws || ws.readyState === WebSocket.CLOSED) {
        connectWebSocket();
      }
    }, 3000);
  };
  
  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    log("❌ WebSocket connection error");
    updateStatus("Connection error", "error");
  };
}

function handleWebSocketMessage(data) {
  const messageType = data.type || 'unknown';
  
  switch (messageType) {
    case 'telegram_message':
      if (data.data && data.data.chat_id && data.data.sender && data.data.text) {
        addMessage(data.data.chat_id, data.data.sender, data.data.text);
      }
      break;
      
    case 'connection':
      log(`✅ ${data.data.message}`);
      break;
      
    case 'heartbeat_response':
      // Silent heartbeat response
      break;
      
    case 'status_update':
      log(`📊 Status: ${data.data.status}`);
      break;
      
    default:
      log(`📥 WebSocket message: ${messageType}`);
      console.log('WebSocket data:', data);
  }
}

// ===== TELEGRAM API =====
async function sendReply(chat_id, text) {
  try {
    updateStatus("Sending reply...", "info");
    
    const response = await fetch(`${SERVER}/api/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: parseInt(chat_id),
        text: text
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      speakFeedback("Đã gửi trả lời.");
      updateStatus("✅ Reply sent successfully", "success");
      log(`✅ Reply sent to chat ${chat_id}: ${text.substring(0, 50)}...`);
      
      // Reset status after 3 seconds
      setTimeout(() => {
        updateStatus("Ready - Say 'Hey Viso'", "success");
      }, 3000);
      
    } else {
      const error = await response.json();
      throw new Error(error.detail || 'Unknown error');
    }
  } catch (error) {
    console.error("Send reply error:", error);
    speakFeedback("Lỗi gửi tin nhắn.");
    updateStatus("❌ Failed to send reply", "error");
    log(`❌ Failed to send reply: ${error.message}`);
  }
}

// ===== VOICE COMMAND PROCESSING =====
function handleTranscript(rawText) {
  const text = rawText.trim().toLowerCase();
  log(`🎤 Processing: "${rawText}"`);
  
  // Priority 1: Index-based (most reliable)
  let match = text.match(/(?:reply to|trả lời (?:số)?) (\d+)\s+(.+)/i);
  if (match) {
      const [, index, message] = match;
      return replyByIndex(parseInt(index), message);
  }
  
  // Priority 2: Name with delimiter 
  match = text.match(/reply to (\w+) (?:saying|with|message) (.+)/i);
  if (match) {
      const [, name, message] = match;
      return replyByName(name, message);
  }
  
  // Priority 3: Vietnamese patterns
  match = text.match(/trả lời (\w+)\s+(.+)/i);
  if (match) {
      const [, target, message] = match;
      // Try parsing target as number first, then name
      const index = parseInt(target);
      if (!isNaN(index)) {
          return replyByIndex(index, message);
      } else {
          return replyByName(target, message);
      }
  }
  
  // Priority 4: List commands
  if (text.includes("list") || text.includes("hiển thị") || text.includes("liệt kê")) {
      return listMessages();
  }
  
  // Fallback: Suggest correct format
  speakFeedback("Không nhận dạng lệnh. Hãy nói 'Reply to số 3' hoặc 'List messages'");
  showSuggestions();
}

function showSuggestions() {
  const suggestions = [
      "Try: 'Reply to 1 hello'",
      "Try: 'Reply to Alice saying hi'", 
      "Try: 'List messages'"
  ];
  
  updateStatus("💡 " + suggestions[Math.floor(Math.random() * suggestions.length)]);
}

// ===== AUDIO PROCESSING =====
function encodeWAV(audioBuffer) {
  const sampleRate = audioBuffer.sampleRate;
  const samples = audioBuffer.getChannelData(0);
  const length = samples.length * 2;
  const buffer = new ArrayBuffer(44 + length);
  const view = new DataView(buffer);
  
  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };
  
  let offset = 0;
  writeString(offset, 'RIFF'); offset += 4;
  view.setUint32(offset, 36 + length, true); offset += 4;
  writeString(offset, 'WAVE'); offset += 4;
  writeString(offset, 'fmt '); offset += 4;
  view.setUint32(offset, 16, true); offset += 4;
  view.setUint16(offset, 1, true); offset += 2;
  view.setUint16(offset, 1, true); offset += 2;
  view.setUint32(offset, sampleRate, true); offset += 4;
  view.setUint32(offset, sampleRate * 2, true); offset += 4;
  view.setUint16(offset, 2, true); offset += 2;
  view.setUint16(offset, 16, true); offset += 2;
  writeString(offset, 'data'); offset += 4;
  view.setUint32(offset, length, true); offset += 4;
  
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
  }
  
  return new Blob([view], { type: 'audio/wav' });
}

async function transcribeAudio(audioBlob) {
  try {
    updateStatus("Transcribing audio...", "info");
    
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioContext = new AudioContext();
    const decodedAudio = await audioContext.decodeAudioData(arrayBuffer);
    const wavBlob = encodeWAV(decodedAudio);
    
    const response = await fetch("https://api-inference.huggingface.co/models/openai/whisper-large-v3", {
      method: "POST",
      headers: { 
        Authorization: `Bearer ${HF_TOKEN}`, 
        "Content-Type": "audio/wav" 
      },
      body: wavBlob
    });
    
    const result = await response.text();
    log(`🎙️ Whisper response: ${result}`);
    
    try {
      const parsed = JSON.parse(result);
      return parsed.text || "";
    } catch {
      return "";
    }
  } catch (error) {
    console.error("Transcription error:", error);
    updateStatus("❌ Transcription failed", "error");
    return "";
  }
}

// ===== VOICE RECORDING =====
function detectSilence(stream) {
  audioContext = new AudioContext();
  micSource = audioContext.createMediaStreamSource(stream);
  analyser = audioContext.createAnalyser();
  micSource.connect(analyser);
  
  const bufferLength = analyser.fftSize;
  const dataArray = new Uint8Array(bufferLength);
  
  function checkSilence() {
    analyser.getByteTimeDomainData(dataArray);
    
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      const value = (dataArray[i] - 128) / 128;
      sum += value * value;
    }
    
    const rms = Math.sqrt(sum / bufferLength);
    
    if (rms < 0.01) { // Silence threshold
      if (!silenceTimer) {
        silenceTimer = setTimeout(() => {
          log("🔇 Silence detected - stopping recording");
          stopRecording(stream);
        }, 2000); // 2 seconds of silence
      }
    } else {
      if (silenceTimer) {
        clearTimeout(silenceTimer);
        silenceTimer = null;
      }
    }
    
    if (mediaRecorder && mediaRecorder.state === "recording") {
      requestAnimationFrame(checkSilence);
    }
  }
  
  requestAnimationFrame(checkSilence);
}

async function startRecording() {
  try {
    log("🎤 Wake word detected - starting recording");
    updateStatus("🎤 Recording...", "info");
    
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      } 
    });
    
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    });
    
    audioChunks = [];
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };
    
    mediaRecorder.onstop = async () => {
      try {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const transcript = await transcribeAudio(audioBlob);
        
        if (transcript && transcript.trim()) {
          log(`✅ Transcription: "${transcript}"`);
          handleTranscript(transcript);
        } else {
          log("❌ No transcription detected");
          updateStatus("No speech detected", "warning");
          speakFeedback("Không nghe thấy gì. Thử lại.");
        }
      } catch (error) {
        console.error("Recording processing error:", error);
        updateStatus("❌ Processing failed", "error");
      } finally {
        updateStatus("Ready - Say 'Hey Viso'", "success");
      }
    };
    
    mediaRecorder.start();
    detectSilence(stream);
    
  } catch (error) {
    console.error("Recording error:", error);
    updateStatus("❌ Microphone access failed", "error");
    speakFeedback("Không thể truy cập microphone.");
  }
}

function stopRecording(stream) {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    stream.getTracks().forEach(track => track.stop());
    
    if (audioContext) {
      audioContext.close();
    }
    
    if (silenceTimer) {
      clearTimeout(silenceTimer);
      silenceTimer = null;
    }
  }
}

// ===== WAKE WORD DETECTION =====
async function initializePorcupine() {
  try {
    log("🐷 Initializing Porcupine wake word detection...");
    
    const porcupine = await PorcupineWeb.PorcupineWorker.create(
      PORCUPINE_KEY,
      [
        {
          label: "Hey Viso",
          publicPath: "/Hey-Viso_en_wasm_v3_0_0.ppn"
        }
      ],
      () => {
        log("👂 Wake word 'Hey Viso' detected!");
        startRecording();
      },
      {
        publicPath: "/porcupine_params.pv"
      }
    );
    
    await window.WebVoiceProcessor.WebVoiceProcessor.subscribe(porcupine);
    log("✅ Porcupine initialized successfully");
    updateStatus("Ready - Say 'Hey Viso'", "success");
    
  } catch (error) {
    console.error("Porcupine initialization failed:", error);
    log("❌ Porcupine failed - using click to record fallback");
    updateStatus("Click to record (Porcupine failed)", "warning");
    
    // Fallback: click to record
    document.body.addEventListener('click', () => {
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        startRecording();
      }
    });
  }
}

// ===== INITIALIZATION =====
async function initializeApp() {
  log("🚀 Initializing Telegram Voice Reply App");
  
  // Connect to WebSocket
  connectWebSocket();
  
  // Initialize wake word detection
  await initializePorcupine();
  
  // Add some sample data for testing
  setTimeout(() => {
    if (recentMsgs.length === 0) {
      log("📝 Adding sample messages for testing");
      addMessage(123456789, "Alice Johnson", "Hello! How are you today?");
      addMessage(987654321, "Bob Smith", "Can you call me back later?");
      addMessage(555666777, "Carol White", "The meeting is at 3 PM tomorrow");
    }
  }, 2000);
  
  log("✅ App initialization completed");
}

// ===== EXPORT FUNCTIONS FOR COMPATIBILITY =====
window.handleTranscript = handleTranscript;
window.addMessage = addMessage;
window.sendReply = sendReply;

// ===== START THE APP =====
document.addEventListener('DOMContentLoaded', () => {
  // Add some CSS for status colors
  const style = document.createElement('style');
  style.textContent = `
    .status-success { color: #28a745; }
    .status-info { color: #17a2b8; }
    .status-warning { color: #ffc107; }
    .status-error { color: #dc3545; }
  `;
  document.head.appendChild(style);
  
  // Initialize the app
  initializeApp();
});