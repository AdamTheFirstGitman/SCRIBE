"""
Audio transcription service using OpenAI Whisper
Handles multiple audio formats with caching and optimization
"""

import asyncio
import base64
import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile
import os

from openai import AsyncOpenAI

from config import settings
from services.cache import cache_manager
from utils.logger import get_logger, performance_logger, cost_logger

logger = get_logger(__name__)

class TranscriptionService:
    """
    Audio transcription service with intelligent caching and optimization
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.supported_formats = settings.ALLOWED_AUDIO_FORMATS
        self.max_file_size = 25 * 1024 * 1024  # 25MB Whisper limit

    async def transcribe_audio(
        self,
        audio_data: str,
        format: str = "webm",
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text

        Args:
            audio_data: Base64 encoded audio data
            format: Audio format (webm, mp3, wav, etc.)
            language: Optional language hint (e.g., 'fr', 'en')
            prompt: Optional context prompt to improve accuracy

        Returns:
            Dict with transcription results
        """
        start_time = time.time()

        try:
            # Validate format
            if format.lower() not in [f.lower() for f in self.supported_formats]:
                raise ValueError(f"Unsupported audio format: {format}. Supported: {self.supported_formats}")

            # Generate cache key based on audio content
            audio_hash = self._generate_audio_hash(audio_data)

            # Check cache first
            cached_result = await cache_manager.get_transcription(audio_hash)
            if cached_result:
                logger.info("Using cached transcription", audio_hash=audio_hash[:16])
                return cached_result

            # Decode base64 audio
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                raise ValueError(f"Invalid base64 audio data: {str(e)}")

            # Check file size
            if len(audio_bytes) > self.max_file_size:
                raise ValueError(f"Audio file too large: {len(audio_bytes)} bytes (max: {self.max_file_size})")

            # Create temporary file for Whisper API
            temp_file_path = None
            try:
                temp_file_path = await self._create_temp_audio_file(audio_bytes, format)

                # Call Whisper API
                transcription_result = await self._call_whisper_api(
                    temp_file_path, language, prompt
                )

                # Calculate duration and other metrics
                duration_seconds = await self._estimate_audio_duration(audio_bytes, format)
                processing_time_ms = (time.time() - start_time) * 1000

                # Format result
                result = {
                    "text": transcription_result["text"],
                    "confidence": self._estimate_confidence(transcription_result),
                    "duration_seconds": duration_seconds,
                    "language": transcription_result.get("language"),
                    "processing_time_ms": processing_time_ms,
                    "audio_format": format,
                    "audio_size_bytes": len(audio_bytes),
                    "cached": False
                }

                # Log performance
                performance_logger.log_api_call(
                    service="openai_whisper",
                    endpoint="transcriptions",
                    duration_ms=processing_time_ms,
                    status_code=200
                )

                # Log costs
                cost = self._calculate_transcription_cost(duration_seconds)
                cost_logger.log_token_usage(
                    service="openai",
                    model="whisper-1",
                    tokens=int(duration_seconds * 60),  # Rough token estimate
                    cost=cost
                )

                result["cost_eur"] = cost

                # Cache result
                await cache_manager.set_transcription(audio_hash, result)

                logger.info("Audio transcription completed",
                           duration_seconds=duration_seconds,
                           text_length=len(result["text"]),
                           processing_time_ms=processing_time_ms)

                return result

            finally:
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        logger.warning("Failed to cleanup temp file", path=temp_file_path, error=str(e))

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error("Audio transcription failed",
                        format=format,
                        error=str(e),
                        processing_time_ms=processing_time_ms)
            raise

    async def _call_whisper_api(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call OpenAI Whisper API"""

        try:
            with open(audio_file_path, "rb") as audio_file:
                # Prepare API parameters
                params = {
                    "model": "whisper-1",
                    "response_format": "verbose_json",  # Get more detailed response
                }

                if language:
                    params["language"] = language

                if prompt:
                    # Use prompt to improve accuracy for specific contexts
                    params["prompt"] = prompt

                # Call Whisper API
                response = await self.client.audio.transcriptions.create(
                    file=audio_file,
                    **params
                )

                return {
                    "text": response.text,
                    "language": getattr(response, "language", None),
                    "duration": getattr(response, "duration", None),
                    "segments": getattr(response, "segments", [])
                }

        except Exception as e:
            logger.error("Whisper API call failed", error=str(e))
            raise

    async def _create_temp_audio_file(self, audio_bytes: bytes, format: str) -> str:
        """Create temporary audio file for API call"""

        try:
            # Create temporary file with appropriate extension
            suffix = f".{format.lower()}"

            # Use asyncio to handle file operations
            temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="whisper_")

            # Write audio data
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(audio_bytes)

            return temp_path

        except Exception as e:
            logger.error("Failed to create temporary audio file", error=str(e))
            raise

    async def _estimate_audio_duration(self, audio_bytes: bytes, format: str) -> float:
        """Estimate audio duration (simplified)"""
        try:
            # This is a rough estimation based on file size and format
            # For more accurate duration, would need audio processing library

            if format.lower() in ["mp3", "m4a"]:
                # Compressed formats: rough estimate based on bitrate
                estimated_bitrate = 128  # kbps
                duration = (len(audio_bytes) * 8) / (estimated_bitrate * 1000)
            elif format.lower() in ["wav", "webm", "ogg"]:
                # Less compressed: different estimation
                estimated_bitrate = 256  # kbps
                duration = (len(audio_bytes) * 8) / (estimated_bitrate * 1000)
            else:
                # Generic estimation
                duration = len(audio_bytes) / 16000  # Assume 16kHz sample rate

            # Clamp to reasonable values
            return max(0.1, min(duration, 3600))  # Between 0.1s and 1 hour

        except Exception as e:
            logger.warning("Failed to estimate audio duration", error=str(e))
            return 30.0  # Default estimate

    def _estimate_confidence(self, transcription_result: Dict[str, Any]) -> float:
        """Estimate transcription confidence from Whisper response"""
        try:
            # Whisper doesn't provide direct confidence scores
            # We'll estimate based on available information

            text = transcription_result.get("text", "")
            segments = transcription_result.get("segments", [])

            if not text.strip():
                return 0.0

            # Basic heuristics for confidence estimation
            confidence = 0.8  # Base confidence

            # Adjust based on text characteristics
            if len(text) < 10:
                confidence -= 0.2  # Very short transcriptions are less reliable

            if any(char in text for char in "[?]()"):
                confidence -= 0.1  # Uncertain markers

            # If we have segments, use their information
            if segments:
                # Average confidence from segments if available
                segment_confidences = []
                for segment in segments:
                    # Some Whisper implementations provide segment-level confidence
                    if "confidence" in segment:
                        segment_confidences.append(segment["confidence"])

                if segment_confidences:
                    confidence = sum(segment_confidences) / len(segment_confidences)

            return max(0.0, min(confidence, 1.0))

        except Exception as e:
            logger.warning("Failed to estimate confidence", error=str(e))
            return 0.7  # Default confidence

    def _calculate_transcription_cost(self, duration_seconds: float) -> float:
        """Calculate transcription cost in EUR"""
        # OpenAI Whisper pricing: $0.006 per minute
        cost_per_minute_usd = 0.006
        duration_minutes = duration_seconds / 60.0

        cost_usd = duration_minutes * cost_per_minute_usd
        cost_eur = cost_usd * 0.92  # Convert to EUR

        return round(cost_eur, 4)

    def _generate_audio_hash(self, audio_data: str) -> str:
        """Generate hash for audio data caching"""
        return hashlib.sha256(audio_data.encode()).hexdigest()

    async def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return self.supported_formats.copy()

    async def validate_audio_data(self, audio_data: str, format: str) -> Dict[str, Any]:
        """Validate audio data without transcribing"""
        try:
            # Check format
            if format.lower() not in [f.lower() for f in self.supported_formats]:
                return {
                    "valid": False,
                    "error": f"Unsupported format: {format}",
                    "supported_formats": self.supported_formats
                }

            # Check base64 encoding
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"Invalid base64 encoding: {str(e)}"
                }

            # Check size
            if len(audio_bytes) > self.max_file_size:
                return {
                    "valid": False,
                    "error": f"File too large: {len(audio_bytes)} bytes (max: {self.max_file_size})"
                }

            if len(audio_bytes) < 100:
                return {
                    "valid": False,
                    "error": "Audio data too small, likely corrupted"
                }

            return {
                "valid": True,
                "size_bytes": len(audio_bytes),
                "estimated_duration": await self._estimate_audio_duration(audio_bytes, format),
                "estimated_cost_eur": self._calculate_transcription_cost(
                    await self._estimate_audio_duration(audio_bytes, format)
                )
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }

# Global transcription service instance
transcription_service = TranscriptionService()