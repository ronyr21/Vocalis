import gradio as gr
import asyncio
import websockets
import json
import base64
import os
import tempfile
import time

# --- Configuration ---
FASTAPI_WS_URL = os.getenv("FASTAPI_WS_URL", "ws://localhost:8000/ws") # Make sure this matches your FastAPI backend

# Global WebSocket connection state
websocket_client = None
ws_listener_task = None
transcription_queue = asyncio.Queue()
llm_response_queue = asyncio.Queue()
tts_audio_queue = asyncio.Queue()
chatbot_history_queue = asyncio.Queue() # For updating chatbot history

# --- WebSocket Communication ---
async def get_websocket_client():
    global websocket_client
    if websocket_client is None or websocket_client.closed:
        try:
            print(f"Attempting to connect to WebSocket: {FASTAPI_WS_URL}")
            websocket_client = await websockets.connect(FASTAPI_WS_URL)
            print("Successfully connected to FastAPI WebSocket.")
            # Start listener task if connection is successful and task is not running
            global ws_listener_task
            if ws_listener_task is None or ws_listener_task.done():
                ws_listener_task = asyncio.create_task(websocket_listener())
                print("WebSocket listener task started/restarted.")
        except Exception as e:
            print(f"Failed to connect to WebSocket: {e}")
            websocket_client = None
    return websocket_client

async def close_websocket_client():
    global websocket_client, ws_listener_task
    if ws_listener_task:
        ws_listener_task.cancel()
        try:
            await ws_listener_task
        except asyncio.CancelledError:
            print("WebSocket listener task cancelled.")
        ws_listener_task = None
    if websocket_client and not websocket_client.closed:
        await websocket_client.close()
        print("WebSocket connection closed.")
    websocket_client = None

async def send_ws_message(message: dict):
    ws = await get_websocket_client()
    if ws:
        try:
            await ws.send(json.dumps(message))
            print(f"Sent to backend: {message.get('type')}")
        except Exception as e:
            print(f"Error sending message: {e}. Attempting to reconnect and retry...")
            await close_websocket_client()
            ws = await get_websocket_client() # Reconnect
            if ws:
                try:
                    await ws.send(json.dumps(message))
                    print(f"Sent to backend (after reconnect): {message.get('type')}")
                except Exception as e_retry:
                    print(f"Error sending message on retry: {e_retry}")
                    await chatbot_history_queue.put({"error": f"Failed to send message: {e_retry}"})
            else:
                print("Failed to reconnect to send message.")
                await chatbot_history_queue.put({"error": "Cannot connect to backend to send message."})
    else:
        print("No WebSocket connection available to send message.")
        await chatbot_history_queue.put({"error": "Not connected to backend."})


async def websocket_listener():
    while True:
        ws = await get_websocket_client()
        if not ws:
            print("Listener: No connection, waiting...")
            await asyncio.sleep(3)
            continue
        try:
            message_json = await ws.recv()
            message = json.loads(message_json)
            msg_type = message.get("type")
            print(f"Listener received: {msg_type}") # Debug

            if msg_type == "transcription":
                text = message.get("text", "")
                await transcription_queue.put(text)
                await chatbot_history_queue.put({"user": text})
            elif msg_type == "llm_response":
                text = message.get("text", "")
                await llm_response_queue.put(text)
            elif msg_type == "tts_chunk":
                audio_b64 = message.get("audio_chunk")
                if audio_b64:
                    await tts_audio_queue.put(base64.b64decode(audio_b64))
            elif msg_type == "tts_end":
                await tts_audio_queue.put(None) # Sentinel for end of TTS stream
            elif msg_type == "status":
                print(f"Backend status: {message.get('status')} - {message.get('data')}")
            elif msg_type == "error":
                print(f"Backend error: {message.get('error')}")
                await chatbot_history_queue.put({"error": f"Backend error: {message.get('error')}"})
        except websockets.exceptions.ConnectionClosed:
            print("Listener: WebSocket connection closed by server. Reconnecting...")
            await close_websocket_client() # Resets client and listener task var
        except Exception as e:
            print(f"Error in WebSocket listener: {e}. Attempting to reset connection.")
            await close_websocket_client()


# --- Gradio Handler Functions ---
async def handle_audio_input(audio_path, text_supplement, chat_history_state_ignored):
    if not audio_path:
        return None, "No audio recorded. Please record audio first.", None

    transcription_text = "Transcription pending..."
    llm_response_text = ""
    tts_output_file = None

    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        await send_ws_message({
            "type": "audio",
            "audio_data": audio_base64,
            "supplementary_text": text_supplement or ""
        })

        timeout = 30  # seconds

        try:
            transcription_text = await asyncio.wait_for(transcription_queue.get(), timeout=timeout/3)
        except asyncio.TimeoutError:
            transcription_text = "Transcription timed out."
            await chatbot_history_queue.put({"error": transcription_text})

        try:
            llm_response_text = await asyncio.wait_for(llm_response_queue.get(), timeout=timeout/3)
        except asyncio.TimeoutError:
            llm_response_text = "AI response timed out."
            await chatbot_history_queue.put({"ai": llm_response_text})

        audio_chunks = []
        try:
            while True:
                chunk = await asyncio.wait_for(tts_audio_queue.get(), timeout=timeout/3)
                if chunk is None:
                    break
                audio_chunks.append(chunk)

            if audio_chunks:
                final_audio_bytes = b"".join(audio_chunks)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                    tmpfile.write(final_audio_bytes)
                    tts_output_file = tmpfile.name
                await chatbot_history_queue.put({"ai": llm_response_text or "(No LLM response)"})
            elif llm_response_text:
                 await chatbot_history_queue.put({"ai": llm_response_text + " (Audio not received)"})

        except asyncio.TimeoutError:
            if llm_response_text:
                await chatbot_history_queue.put({"ai": llm_response_text + " (Audio timed out)"})
            else:
                await chatbot_history_queue.put({"error": "TTS Audio timed out."})

        return transcription_text, tts_output_file

    except Exception as e:
        print(f"Error in handle_audio_input: {e}")
        error_message = f"Error processing audio: {str(e)}"
        await chatbot_history_queue.put({"error": error_message})
        return transcription_text, None


async def handle_text_input(text_input, chat_history_state_ignored):
    if not text_input.strip():
        return None

    await chatbot_history_queue.put({"user": text_input})

    await send_ws_message({ "type": "text_message", "text": text_input })

    llm_response_text = ""
    tts_output_file = None
    timeout = 20

    try:
        llm_response_text = await asyncio.wait_for(llm_response_queue.get(), timeout=timeout/2)
    except asyncio.TimeoutError:
        llm_response_text = "AI response timed out."
        await chatbot_history_queue.put({"ai": llm_response_text})
        return None

    audio_chunks = []
    try:
        while True:
            chunk = await asyncio.wait_for(tts_audio_queue.get(), timeout=timeout/2)
            if chunk is None: break
            audio_chunks.append(chunk)
        if audio_chunks:
            final_audio_bytes = b"".join(audio_chunks)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                tmpfile.write(final_audio_bytes)
                tts_output_file = tmpfile.name
            await chatbot_history_queue.put({"ai": llm_response_text})
        elif llm_response_text:
             await chatbot_history_queue.put({"ai": llm_response_text + " (Audio not received)"})
    except asyncio.TimeoutError:
        if llm_response_text:
            await chatbot_history_queue.put({"ai": llm_response_text + " (Audio timed out)"})
        else:
            await chatbot_history_queue.put({"error": "TTS Audio timed out."})

    return tts_output_file

async def stream_chatbot_display(current_chat_history):
    if current_chat_history is None:
        current_chat_history = []

    yield current_chat_history

    while True:
        try:
            update = await chatbot_history_queue.get()
            if "user" in update:
                current_chat_history.append([update["user"], None])
            elif "ai" in update:
                if current_chat_history and current_chat_history[-1][1] is None:
                    current_chat_history[-1][1] = update["ai"]
                else:
                    current_chat_history.append([None, update["ai"]])
            elif "error" in update:
                current_chat_history.append([None, f"ERROR: {update['error']}"])

            yield current_chat_history

        except Exception as e:
            print(f"Error in stream_chatbot_display: {e}")
            current_chat_history.append([None, f"Chat Display Error: {str(e)}"])
            yield current_chat_history
            await asyncio.sleep(0.1)


# --- Gradio Interface Design ---
with gr.Blocks(title="Vocalis Gradio Client", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Vocalis AI Assistant - Gradio Interface")

    with gr.Row():
        with gr.Column(scale=2):
            chatbot_display = gr.Chatbot(
                label="Conversation", bubble_full_width=False, height=500, avatar_images=(None, "https://raw.githubusercontent.com/gradio-app/gradio/main/gradio/icons/robot.svg")
            )
            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Speak Here")
            text_input_for_audio = gr.Textbox(label="Or type while recording (optional, supplements audio)", placeholder="Type any supplementary text here...")
            submit_audio_button = gr.Button("Send Audio / Get Response")

            text_input_separate = gr.Textbox(label="Or Type Your Message Here", placeholder="Type your message...", show_label=True)
            submit_text_button = gr.Button("Send Typed Message")

        with gr.Column(scale=1):
            gr.Markdown("## AI Response Audio")
            tts_audio_output = gr.Audio(label="Listen to AI Response", type="filepath", autoplay=True)
            gr.Markdown("## Live Transcription")
            transcription_display = gr.Textbox(label="Your Speech Transcribed:", lines=3, interactive=False)

    # Event Handlers
    submit_audio_button.click(
        fn=handle_audio_input,
        inputs=[audio_input, text_input_for_audio, chatbot_display],
        outputs=[transcription_display, tts_audio_output]
    )
    submit_text_button.click(
        fn=handle_text_input,
        inputs=[text_input_separate, chatbot_display],
        outputs=[tts_audio_output]
    )
    text_input_separate.submit( # Allow Enter key
        fn=handle_text_input,
        inputs=[text_input_separate, chatbot_display],
        outputs=[tts_audio_output]
    )

    demo.load(stream_chatbot_display, inputs=chatbot_display, outputs=chatbot_display, every=1) # Periodically refresh chatbot

async def main_async():
    global ws_listener_task
    await get_websocket_client()

    print("Starting Gradio app...")
    demo.queue()
    # Changed share=False for local testing by default
    await demo.launch(server_name="0.0.0.0", server_port=7860, prevent_thread_lock=True, show_error=True, share=False)

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("Gradio app shutting down by user.")
    except Exception as e:
        print(f"Gradio app failed to run: {e}")
    finally:
        print("Cleaning up...")
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running(): # Check if loop is running before trying to manipulate it
                 # Schedule cleanup task and wait for it
                cleanup_task = loop.create_task(close_websocket_client())
                loop.run_until_complete(cleanup_task)
            else:
                 # Fallback if no loop is running, or if it's closed
                asyncio.run(close_websocket_client())
        except Exception as e_cleanup:
            print(f"Error during cleanup: {e_cleanup}")
        print("Exited.")
