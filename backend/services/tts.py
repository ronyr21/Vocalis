"""
Text-to-Speech Service

Handles communication with the local TTS API endpoint.
"""

import json
import requests
import logging
import io
import time
import base64
import asyncio
from typing import Dict, Any, List, Optional, BinaryIO, Generator, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSClient:
    """
    Client for communicating with a local TTS API.

    This class handles requests to a locally hosted TTS API that follows
    the OpenAI API format for text-to-speech generation.
    """

    def __init__(
        self,
        api_endpoint: str = "http://localhost:5005/v1/audio/speech",
        model: str = "tts-1",
        voice: str = "tara",
        output_format: str = "wav",
        speed: float = 1.0,
        timeout: int = 60,
        chunk_size: int = 4096,
    ):
        """
        Initialize the TTS client.

        Args:
            api_endpoint: URL of the local TTS API
            model: TTS model name to use
            voice: Voice to use for synthesis
            output_format: Output audio format (mp3, opus, aac, flac)
            speed: Speech speed multiplier (0.25 to 4.0)
            timeout: Request timeout in seconds
            chunk_size: Size of audio chunks to stream in bytes
        """
        self.api_endpoint = api_endpoint
        self.model = model
        self.voice = voice
        self.output_format = output_format
        self.speed = speed
        self.timeout = timeout
        self.chunk_size = chunk_size

        # State tracking
        self.is_processing = False
        self.last_processing_time = 0

        # Simple cache for frequently used phrases
        # Using a relatively small cache size to prevent memory issues
        self.cache_max_size = 50
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.interrupt_event = threading.Event()

        logger.info(
            f"Initialized TTS Client with endpoint={api_endpoint}, "
            f"model={model}, voice={voice}"
        )

    def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert to speech

        Returns:
            Audio data as bytes
        """
        self.is_processing = True
        start_time = time.time()

        try:
            # Check cache first
            if text in self.cache:
                self.cache_hits += 1
                audio_data = self.cache[text]
                logger.info(
                    f"TTS cache hit for text ({len(text)} chars), cache hits: {self.cache_hits}"
                )
                self.last_processing_time = time.time() - start_time
                return audio_data

            self.cache_misses += 1

            # Prepare request payload
            payload = {
                "model": self.model,
                "input": text,
                "voice": self.voice,
                "response_format": self.output_format,
                "speed": self.speed,
            }

            logger.info(
                f"Sending TTS request with {len(text)} characters of text, cache misses: {self.cache_misses}"
            )

            # Send request to TTS API
            response = requests.post(
                self.api_endpoint, json=payload, timeout=self.timeout
            )

            # Check if request was successful
            response.raise_for_status()

            # Get audio content
            audio_data = response.content

            # Add to cache if not too large
            if len(self.cache) < self.cache_max_size:
                self.cache[text] = audio_data
            elif len(text) < 100:  # Only replace cache items with small text chunks
                # Simple LRU-like strategy - remove a random item
                if self.cache:
                    self.cache.pop(next(iter(self.cache)))
                    self.cache[text] = audio_data

            # Calculate processing time
            self.last_processing_time = time.time() - start_time

            logger.info(
                f"Received TTS response after {self.last_processing_time:.2f}s, "
                f"size: {len(audio_data)} bytes"
            )

            return audio_data

        except requests.RequestException as e:
            logger.error(f"TTS API request error: {e}")
            raise
        except Exception as e:
            logger.error(f"TTS processing error: {e}")
            raise
        finally:
            self.is_processing = False

    def stream_text_to_speech1(self, text: str) -> Generator[bytes, None, None]:
        """
        Stream audio data from the TTS API.

        Args:
            text: Text to convert to speech

        Yields:
            Chunks of audio data
        """
        self.is_processing = True
        start_time = time.time()

        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "input": text,
                "voice": self.voice,
                "response_format": self.output_format,
                "speed": self.speed,
            }

            logger.info(
                f"Sending streaming TTS request with {len(text)} characters of text"
            )

            # Send request to TTS API
            with requests.post(
                self.api_endpoint, json=payload, timeout=self.timeout, stream=True
            ) as response:
                response.raise_for_status()

                # Check if streaming is supported by the API
                is_chunked = response.headers.get("transfer-encoding", "") == "chunked"

                if is_chunked:
                    # The API supports streaming
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            yield chunk
                else:
                    # The API doesn't support streaming, but we'll fake it by
                    # splitting the response into chunks
                    audio_data = response.content
                    total_chunks = (
                        len(audio_data) + self.chunk_size - 1
                    ) // self.chunk_size

                    for i in range(total_chunks):
                        start_idx = i * self.chunk_size
                        end_idx = min(start_idx + self.chunk_size, len(audio_data))
                        yield audio_data[start_idx:end_idx]

            # Calculate processing time
            self.last_processing_time = time.time() - start_time
            logger.info(
                f"Completed TTS streaming after {self.last_processing_time:.2f}s"
            )

        except requests.RequestException as e:
            logger.error(f"TTS API streaming request error: {e}")
            raise
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            raise
        finally:
            self.is_processing = False

    async def stream_text_to_speech(self, text, websocket):
        """
        Stream text to speech and send audio to client

        Args:
            text: Text to convert to speech
            websocket: WebSocket connection to send audio to
        """
        # Reset interrupt flag before starting
        self.interrupt_event.clear()
        # Set processing flag to indicate we're generating speech
        self.is_processing = True

        logger.info(f"Starting TTS for text: {text[:50]}...")

        def generate_chunks():
            try:
                # Get the appropriate streaming endpoint based on config
                stream_endpoint = f"{self.api_endpoint.rstrip('/').replace('/v1/audio/speech', '')}/tts/stream"
                logger.info(f"Using TTS streaming endpoint: {stream_endpoint}")

                # Make the request with streaming enabled
                response = requests.post(
                    stream_endpoint, json={"text": text}, stream=True
                )

                # Check response status
                response.raise_for_status()

                # Track if any interrupts have been processed
                interrupted = False

                # Iterate through chunks, checking interrupt flag frequently
                for chunk in response.iter_content(chunk_size=1024):
                    # Priority check for interrupt before processing chunk
                    if self.interrupt_event.is_set():
                        logger.info("TTS generation interrupted")
                        interrupted = True
                        break

                    # Only yield if not interrupted
                    if chunk and not interrupted:
                        yield chunk

                        # Extra interrupt check immediately after yielding
                        # This provides more responsiveness to interrupts
                        if self.interrupt_event.is_set():
                            logger.info(
                                "TTS generation interrupted after yielding chunk"
                            )
                            interrupted = True
                            break

            except Exception as e:
                logger.error(f"Error in TTS chunk generation: {e}")
                # If error occurs, yield empty chunk to maintain flow
                yield b""

        try:
            # Prepare chunks generator
            chunks = generate_chunks()

            # Send TTS start message before first chunk
            if not self.interrupt_event.is_set():
                await websocket.send_json({"type": "tts_start"})

            # Process chunks and send to websocket
            for chunk in chunks:
                # Immediately stop if interrupted
                if self.interrupt_event.is_set():
                    logger.info("Stopping TTS stream due to interrupt")
                    break

                # Only send non-empty chunks
                if chunk:
                    # Convert chunk to base64 for JSON transport
                    b64_chunk = base64.b64encode(chunk).decode("utf-8")

                    # Send chunk as JSON with type and format
                    await websocket.send_json(
                        {"type": "tts_chunk", "audio_chunk": b64_chunk, "format": "wav"}
                    )

                    # Check interrupt again immediately after sending
                    if self.interrupt_event.is_set():
                        logger.info("Interrupt detected after sending chunk")
                        break

            # Always send TTS end message, even if interrupted
            await websocket.send_json({"type": "tts_end"})

            if self.interrupt_event.is_set():
                logger.info("TTS stream completed (interrupted)")
            else:
                logger.info("TTS stream completed normally")

        except Exception as e:
            logger.error(f"Error during TTS streaming: {e}")
            # Try to send error if websocket is still open
            try:
                await websocket.send_json(
                    {"type": "error", "error": f"TTS error: {str(e)}"}
                )
            except:
                pass
        finally:
            # Always reset processing flag
            self.is_processing = False

    async def async_text_to_speech(self, text: str) -> bytes:
        """
        Asynchronously generate audio data from the TTS API.

        This method provides asynchronous TTS capability by running
        the synchronous method in a thread.

        Args:
            text: Text to convert to speech

        Returns:
            Complete audio data as bytes
        """
        self.is_processing = True

        try:
            # Check cache first (fast path, no need for async)
            if text in self.cache:
                self.cache_hits += 1
                logger.info(f"Async TTS cache hit for text ({len(text)} chars)")
                return self.cache[text]

            # For larger chunks, process in a thread pool to not block the event loop
            logger.info(f"Async TTS request for text ({len(text)} chars)")
            start_time = time.time()
            audio_data = await asyncio.to_thread(self.text_to_speech, text)
            processing_time = time.time() - start_time
            self.last_processing_time = processing_time

            # Store in cache after successful generation
            self.cache[text] = audio_data

            logger.info(f"Async TTS completed in {processing_time:.3f}s")
            return audio_data

        except Exception as e:
            logger.error(f"Async TTS error: {e}")
            # Return empty audio on error
            return b""
        finally:
            self.is_processing = False

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.

        Returns:
            Dict containing the current configuration
        """
        return {
            "api_endpoint": self.api_endpoint,
            "model": self.model,
            "voice": self.voice,
            "output_format": self.output_format,
            "speed": self.speed,
            "timeout": self.timeout,
            "chunk_size": self.chunk_size,
            "is_processing": self.is_processing,
            "last_processing_time": self.last_processing_time,
        }

    def reset_state(self):
        """
        Forcibly reset the TTS client state.

        This is used when operations need to be interrupted immediately,
        such as when a user interrupts ongoing TTS playback.
        """
        logger.info("Forcibly resetting TTS client state")
        self.is_processing = False
        self.interrupt_event.set()  # Signal any ongoing streaming to stop


# Look for batch_size or generation parameters that could be tuned for speed
# This is typically specific to the TTS implementation being used
# Common optimizations include:
# - Lower quality parameter values
# - Smaller batch sizes
# - Caching frequently used phrases
# - Setting streaming mode flags where available
