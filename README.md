![Vocalis - Speech-to-Speech AI Assistant](https://lex-au.github.io/Vocalis/Vocalis_Header.png)

# Vocalis

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Whisper](https://img.shields.io/badge/Whisper-Faster--Whisper-yellow.svg)](https://github.com/guillaumekln/faster-whisper)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)

Vocalis is a backend-only Python application providing an API for sophisticated speech-to-speech capabilities. It uses a FastAPI backend for a responsive, low-latency conversational experience.

## Changelog

**v1.5.0** (Vision Update) - April 12, 2025
- 🔍 New image analysis capability powered by [SmolVLM-256M-Instruct model](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)
- 🔄 Contextual conversation continuation based on image understanding
- 🧩 Multi-modal conversation support (text, speech, and images)
- 💾 Advanced session management (backend capability) for saving and retrieving conversations

**v1.0.0** (Initial Release) - March 31, 2025
- ✨ Revolutionary barge-in technology for natural conversation flow
- 🔊 Ultra low-latency audio streaming with adaptive buffering
- 🤖 AI-initiated greetings and follow-ups for natural conversations
- 🔄 Streaming TTS with chunk-based delivery for immediate responses
- 🚀 Cross-platform support with optimised setup scripts
- 💻 CUDA acceleration with fallback for CPU-only systems

## Features

### 🎯 Advanced Conversation Capabilities

- **🗣️ Barge-In Interruption** - Interrupt the AI mid-speech for a truly natural conversation experience
- **👋 AI-Initiated Greetings** - Assistant automatically welcomes users with a contextual greeting
- **💬 Intelligent Follow-Ups** - System detects silence and continues conversation with natural follow-up questions
- **🔄 Conversation Memory** - Maintains context throughout the conversation session
- **🧠 Contextual Understanding** - Processes conversation history for coherent, relevant responses
- **🖼️ Image Analysis** - Backend support for image analysis when image data is provided.
- **💾 Session Management** - Backend capability to save, load, and manage conversation sessions.

### ⚡ Ultra-Responsive Performance

- **⏱️ Low-Latency Processing** - End-to-end latency under 500ms for immediate response perception
- **🔊 Streaming Audio** - Begin playback before full response is generated
- **📦 Adaptive Buffering** - Dynamically adjust audio buffer size based on network conditions
- **🔌 Efficient WebSocket Protocol** - Bidirectional real-time audio streaming
- **🔄 Parallel Processing** - Multi-stage pipeline for concurrent audio handling

### 🛠️ Technical Excellence

- **🔍 High-Accuracy VAD** - Superior voice activity detection using custom-built VAD
- **🗣️ Optimised Whisper Integration** - Faster-Whisper for rapid transcription
- **🔊 Real-Time TTS** - Chunked audio delivery for immediate playback
- **🖥️ Hardware Flexibility** - CUDA acceleration with CPU fallback options
- **🔧 Easy Configuration** - Environment variables and user-friendly setup

## Quick Start

### Prerequisites

#### Windows
- Python 3.10+ installed and in your PATH

#### macOS
- Python 3.10+ installed
- **Apple Silicon (M1/M2/M3/M4) Notes**:
  - The setup will automatically install a compatible PyTorch version
  - If you encounter any PyTorch-related errors, you may need to manually install it:
    ```bash
    pip install torch
    ```
    Then continue with the regular setup.

### One-Click Setup (Recommended)

#### Windows
1. Run `setup.bat` to initialise the project (one-time setup)
   - Includes option for CUDA or CPU-only PyTorch installation
2. Run `run.bat` to start the backend server
3. If you need to update dependencies later, use `install-deps.bat`

#### macOS/Linux
1. Make scripts executable: `chmod +x *.sh`
2. Run `./setup.sh` to initialise the project (one-time setup)
   - Includes option for CUDA or CPU-only PyTorch installation
3. Run `./run.sh` to start the backend server
4. If you need to update dependencies later, use `./install-deps.sh`

### Manual Setup (Alternative)

If you prefer to set up the project manually, follow these steps:

#### Backend Setup
1. Create a Python virtual environment:
   ```bash
   cd backend
   python -m venv env
   # Windows:
   .\env\Scripts\activate
   # macOS/Linux:
   source env/bin/activate
   ```

2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. If you need CUDA support, install PyTorch with CUDA:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   ```

4. Start the backend server:
   ```bash
   python -m backend.main
   ```

## External Services

Vocalis is designed to work with OpenAI-compatible API endpoints for both LLM and TTS services:

- **LLM (Language Model)**: By default, the backend is configured to use [LM Studio](https://lmstudio.ai/) running locally. This provides a convenient way to run local language models compatible with OpenAI's API format.
  
  **Custom Vocalis Model**: For optimal performance, Vocalis includes a purpose-built fine-tuned model: [lex-au/Vocalis-Q4_K_M.gguf](https://huggingface.co/lex-au/Vocalis-Q4_K_M.gguf). This model is based on Meta's LLaMA 3 8B Instruct and specifically optimised for immersive conversational experiences with:
  - Enhanced spatial and temporal context tracking
  - Low-latency response generation
  - Rich, descriptive language capabilities
  - Efficient resource utilisation through Q4_K_M quantisation
  - Seamless integration with the Vocalis speech-to-speech pipeline

- **Text-to-Speech (TTS)**: For voice generation, the system works out of the box with:
  - [Orpheus-FASTAPI](https://github.com/Lex-au/Orpheus-FastAPI): A high-quality TTS server with OpenAI-compatible endpoints providing rich, expressive voices.
  
  You can adjust the endpoint in `.env` to any opensource TTS project. For a lightning-fast alternative:
  - [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI): A lightning-fast TTS alternative, optimised for minimal latency when speed is the priority over maximum expressiveness.

Both services can be configured in the `backend/.env` file. The system requires these external services to function properly, as Vocalis acts as an orchestration layer combining speech recognition, language model inference, and speech synthesis.

## Session Management

Vocalis includes a robust backend session management system that allows users to save, load, and organise their conversations:

### Key Features

- **Save Conversations**: Backend can save the current conversation state with a custom title
- **Load Previous Sessions**: Backend can return to any saved conversation
- **Edit Session Titles**: Backend can rename sessions for better organisation
- **Delete Unwanted Sessions**: Backend can remove conversations
- **Session Metadata**: Backend can provide additional information like message count
- **Automatic Timestamps**: Sessions track both creation and last update times

### Technical Implementation

The session system uses a backend storage architecture:

- Conversations are stored as JSON files in a dedicated directory
- Each session maintains its complete message history
- Asynchronous file I/O prevents performance impacts
- UUID-based session identification ensures uniqueness

This persistent storage system ensures you never lose valuable conversations and can maintain separate contexts for different topics or projects.

### Image Analysis Process

Vocalis now includes visual understanding capabilities through the SmolVLM-256M-Instruct model:

1. **Image Data Reception**:
   - The backend API can receive image data (e.g., as base64 encoded strings).
   - This data can be sent via API requests.

2. **Vision Processing**:
   - The SmolVLM model processes the image data with transformers.
   - The model generates a detailed description of the image contents.
   - This description is added to the conversation context.

3. **Contextual Continuation**:
   - After image processing, API clients can send questions about the image.
   - The system maintains awareness of the image context.
   - Responses are generated with understanding of the visual content.

### Streaming Architecture Features

1. **Parallel Processing**:
   - Simultaneous audio generation and transmission.
   - Non-blocking pipeline for maximum responsiveness.

2. **Barge-in Capability**:
   - Real-time voice activity detection during AI speech.
   - Multi-level interrupt system with priority handling.
   - Immediate pipeline clearing for zero-latency response to interruptions.

3. **Audio Buffer Management**:
   - Adaptive buffer sizes based on network conditions (20-50ms chunks).
   - Efficient audio format selection (Opus for compression, PCM for quality).

4. **Silence Response System**:
   - Time-based silence detection with configurable thresholds.
   - Context-aware follow-up generation.
   - Natural cadence for conversation flow maintenance.

### Implementation Details:

1. **Backend TTS Integration**:
   - Configure TTS API with streaming support if available.
   - Implement custom chunking if necessary.

2. **Custom Streaming Implementation**:
   - Set up an async generator in FastAPI.
   - Split audio into small chunks (10-50ms).
   - Send each chunk immediately through WebSocket.

3. **WebSocket Protocol Enhancement**:
   - Message types for different audio events remain relevant for API clients:
     - `audio_chunk`: A piece of TTS audio.
     - `audio_start`: Signal to prepare for audio context.
     - `audio_end`: Signal that the complete utterance is finished.

### Technical Considerations:

1. **Chunk Size Tuning**:
   - Find optimal balance between network overhead and latency.

2. **Buffer Management**:
   - Avoid buffer underrun and excessive buffering on the client (if applicable).

3. **Format Efficiency**:
   - Use efficient audio formats for streaming (Opus, WebM, or raw PCM).

4. **Abort Capability**:
   - Implement clean interruption for new user input via API signals.

## Buffer Management Approach

### 1. Adaptive Buffer Sizing
- Start with small buffers (20-30ms) for sending audio.
- Monitor transmission stability.
- Dynamically adjust buffer size based on network conditions if feedback is available.

### 2. Parallel Processing Pipeline
- Process audio in parallel streams where possible.
- Begin TTS transmission as soon as first chunk is available.
- Continue processing subsequent chunks during transmission.

### 3. Interrupt Handling
- Implement a "barge-in" capability where new API signals can cancel ongoing TTS.
- Clear audio generation immediately on interruption.

## Latency Optimisation

Vocalis achieves exceptional low-latency performance through carefully optimised components:

### Speech Recognition Performance

The system uses Faster-Whisper with the `base.en` model and a beam size of 2, striking an optimal balance between accuracy and speed. This configuration achieves:

- **ASR Processing**: ~0.43 seconds for typical utterances
- **Response Generation**: ~0.18 seconds
- **Total Round-Trip Latency**: ~0.61 seconds

Real-world example from system logs:
```
INFO:faster_whisper:Processing audio with duration 00:02.229
INFO:backend.services.transcription:Transcription completed in 0.51s: Hi, how are you doing today?...
INFO:backend.services.tts:Sending TTS request with 147 characters of text
INFO:backend.services.tts:Received TTS response after 0.16s, size: 390102 bytes
```

### Customising Performance

You can adjust these settings to optimise for your specific needs:

1. **Model Size**: In `.env`, modify `WHISPER_MODEL=base.en` 
   - Options: tiny.en, base.en, small.en, medium.en, large
   - Smaller models = faster processing, potentially lower accuracy
   - Larger models = more accurate, but increased latency

2. **Beam Size**: In `backend/services/transcription.py`, modify the `beam_size` parameter
   - Default: 2
   - Range: 1-5 (1 = fastest, 5 = most accurate)
   - Located in the `__init__` method of the `WhisperTranscriber` class

### Latency vs. Accuracy Trade-offs

| Model | Beam Size | Approximate ASR Time | Accuracy |
|------|-----------|---------------------|----------|
| tiny.en | 1 | ~0.01s | Lower |
| base.en | 2 | ~0.03s | Good |
| small.en | 3 | ~0.10s | Better |
| medium.en | 4 | ~0.25s | Very Good |
| large | 5 | ~0.50s | Best |

With optimisations in place, Vocalis can achieve total processing latencies well under 250ms when using smaller models, which is typically perceived as "immediate" by users.

## Project Structure

```
Vocalis/
├── README.md
├── setup.bat            # Windows one-time setup script
├── run.bat              # Windows run script 
├── install-deps.bat     # Windows dependency update script
├── setup.sh             # Unix one-time setup script
├── run.sh               # Unix run script
├── install-deps.sh      # Unix dependency update script
├── conversations/       # Directory for saved session files
├── backend/
│   ├── .env
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── services/
│   │   ├── __init__.py
│   │   ├── conversation_storage.py
│   │   ├── llm.py
│   │   ├── transcription.py  # Includes VAD functionality
│   │   ├── tts.py
│   │   ├── vision.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── websocket.py
```

## Dependencies

### Backend (Python)
```
fastapi==0.109.2
uvicorn==0.27.1
python-dotenv==1.0.1
websockets==12.0
numpy==1.26.4
transformers
faster-whisper==1.1.1
requests==2.31.0
python-multipart==0.0.9
torch==2.0.1
ctranslate2==3.10.0
ffmpeg-python==0.2.0
```

## Technical Decisions

- **Audio Format**: API expects audio data in a common format (e.g., WAV, PCM). Specifics to be detailed in API documentation.
- **Error Handling**: Robust error handling with informative API error responses.
- **Conversation Model**: Multi-turn with context preservation.
- **Vision Processing**: SmolVLM-256M-Instruct for efficient image understanding.
- **Session Storage**: Asynchronous JSON file-based persistence with UUID identifiers.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.