from __future__ import annotations

import asyncio
import datetime
import json
import os
from typing import Any
from typing import Dict

from api.dependencies import get_audio_stream_accumulator
from api.dependencies import get_intent_service_ws
from api.dependencies import get_orchestration_service_ws
from api.helpers.audio_stream_accumulator import AudioStreamAccumulator
from api.helpers.jwt_auth import verify_token
from application.services.intent_service import IntentUnderstandingService
from application.services.orchestration_service import OrchestrationService
from fastapi import APIRouter
from fastapi import Depends
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from shared.logging import get_logger

logger = get_logger('voice')
router = APIRouter(prefix='/voice', tags=['Voice Input'])


class VoiceConnectionManager:
    """Manage WebSocket connections for voice input"""

    def __init__(self):
        self.active_connections = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f'User {user_id} connected to voice input')

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f'User {user_id} disconnected from voice input')

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = VoiceConnectionManager()


@router.websocket('/stream')
async def voice_stream(
    websocket: WebSocket,
    token: str,
    audio_accumulator: AudioStreamAccumulator = Depends(get_audio_stream_accumulator),
    intent_service: IntentUnderstandingService = Depends(get_intent_service_ws),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service_ws),
):
    """
    WebSocket endpoint for voice input streaming.
    Uses AudioStreamAccumulator for efficient audio processing.
    """
    user_id = None
    try:
        # Validate token
        token_data = verify_token(token)
        user_id = str(token_data.user_id)

        await manager.connect(user_id, websocket)

        # Send connection confirmation
        await websocket.send_json({'type': 'connected', 'message': 'Voice stream connected'})

        # Session state
        session_data: Dict[str, Any] = {
            'hint_intent_type': None,  # Intent type from current screen
            'form_data': {},  # Existing form data from screen
            'is_recording': False,
        }

        # Start new session in accumulator
        audio_accumulator.start_new_session()

        # Callback for when a segment is processed
        async def on_segment_processed(seg_id: int, text: str):
            """Send intermediate transcription to client"""
            logger.debug(f'Segment {seg_id} processed: {text}')
            await websocket.send_json({
                'type': 'partial_transcript',
                'segment_id': seg_id,
                'text': text,
            })

        # Set callback
        audio_accumulator.on_segment = on_segment_processed

        while True:
            try:
                # Receive data from frontend
                message = await websocket.receive()

                # Handle JSON messages
                if 'text' in message:
                    data = json.loads(message['text'])
                    message_type = data.get('type')

                    if message_type == 'init':
                        # Initial message with optional form context
                        hint_intent_type = data.get('intent_type')
                        form_data = data.get('form_data', {})

                        session_data['hint_intent_type'] = hint_intent_type
                        session_data['form_data'] = form_data
                        session_data['is_recording'] = True

                        logger.info('Voice session initialized')
                        logger.info(f'  Hint intent: {hint_intent_type}')
                        logger.info(f'  Form data: {form_data}')

                        await websocket.send_json({
                            'type': 'init_ack',
                            'message': 'Session initialized, ready to receive audio',
                        })

                    elif message_type == 'stop_recording':
                        # User clicked ✓ (Stop & Save) - process the recording
                        logger.info('Stop recording requested')

                        session_data['is_recording'] = False

                        try:
                            final_text = await audio_accumulator.get_transcription(auto_reset=True)

                            logger.info(f'Final transcription: "{final_text}"')

                            if not final_text or not final_text.strip():
                                await websocket.send_json({
                                    'type': 'error',
                                    'error': 'Could not transcribe audio. Please try again.',
                                })
                                continue

                            # Step 3: Intent Understanding
                            logger.info('Extracting intent...')
                            intent_result = await intent_service.extract_intent_and_params(
                                text=final_text,
                                form_data=session_data['form_data'],
                                hint_intent_type=session_data['hint_intent_type'],
                            )

                            intent_type = intent_result['intent_type']
                            parameters = intent_result['parameters']

                            logger.info(f'Intent: {intent_type}')
                            logger.info(f'Parameters: {parameters}')

                            # Step 4: Check if intent changed
                            intent_changed = (
                                session_data['hint_intent_type'] is not None
                                and intent_type != session_data['hint_intent_type']
                            )

                            # Step 5: Get plugin to check if needs confirmation
                            from domain.plugins.registry import get_plugin_registry
                            plugin_registry = get_plugin_registry()
                            plugin = plugin_registry.get_plugin(intent_type)

                            needs_confirmation = True  # Default to True for safety
                            if plugin:
                                # Check if plugin requires confirmation for voice input
                                needs_confirmation = plugin.requires_voice_confirmation

                            logger.info(f'🔍 Plugin check: {intent_type}, needs_confirmation={needs_confirmation}')

                            # Step 6: Prepare response
                            response_data = {
                                'type': 'intent_extracted',
                                'asr_text': final_text,
                                'normalized_text': final_text,
                                'intent_type': intent_type,
                                'parameters': parameters,
                                'intent_changed': intent_changed,
                                'needs_confirmation': needs_confirmation,
                            }

                            logger.info(f'Sending response: intent_changed={intent_changed}, needs_confirmation={needs_confirmation}')
                            await websocket.send_json(response_data)

                        except Exception as e:
                            logger.error(f'Error processing recording: {e}', exc_info=True)
                            await websocket.send_json({
                                'type': 'error',
                                'error': f'Failed to process recording: {str(e)}',
                            })

                    elif message_type == 'confirm_execute':
                        # User confirmed the intent execution
                        intent_type = data.get('intent_type')
                        parameters = data.get('parameters', {})

                        try:
                            # Execute via orchestration service
                            result = await orchestration_service.execute_intent(
                                user_id=int(user_id),
                                intent_type=intent_type,
                                parameters=parameters,
                            )

                            # Send success response
                            await websocket.send_json({
                                'type': 'execution_success',
                                'success': result.success,
                                'message': result.message,
                                'data': result.data,
                            })

                            logger.info(f'✅ Execution completed: {result.message}')

                        except Exception as e:
                            logger.error(f'Error executing intent: {e}', exc_info=True)
                            await websocket.send_json({
                                'type': 'execution_error',
                                'error': str(e),
                            })

                    elif message_type == 'cancel':
                        # User clicked ✕ (Cancel) - discard everything
                        logger.info('❌ User cancelled voice input')
                        session_data['is_recording'] = False

                        # Reset accumulator to discard all buffered audio
                        audio_accumulator.reset_state()

                        await websocket.send_json({
                            'type': 'cancelled',
                            'message': 'Voice input cancelled',
                        })

                    elif message_type == 'ping':
                        await websocket.send_json({'type': 'pong'})

                    else:
                        logger.warning(f'Unknown message type: {message_type}')

                # Handle binary audio chunks
                elif 'bytes' in message:
                    audio_chunk = message['bytes']

                    # Add chunk to accumulator for processing
                    await audio_accumulator.add_chunk(audio_chunk)

                    chunk_size = len(audio_chunk)

                    logger.debug(f'>>> Audio chunk received: {chunk_size} bytes')

                    # Send acknowledgment
                    await websocket.send_json({
                        'type': 'audio_chunk_ack',
                        'chunk_size': chunk_size,
                    })

                else:
                    logger.warning(f'Unknown message format: {message}')
                    # Check if it's a disconnect message
                    if message.get('type') == 'websocket.disconnect':
                        logger.info('Client disconnected')
                        break
                    continue

            except json.JSONDecodeError as e:
                logger.error(f'Failed to parse JSON: {e}')
                await websocket.send_json({
                    'type': 'error',
                    'error': 'Invalid JSON format',
                })
                continue
            except Exception as e:
                logger.error(f'Error receiving message: {e}')
                break

    except WebSocketDisconnect:
        # Clean up on disconnect
        logger.info('WebSocket disconnecting - cleaning up resources')
        audio_accumulator.reset_state()
        if user_id:
            manager.disconnect(user_id)
        logger.info('WebSocket disconnected')
    except Exception as e:
        logger.error(f'WebSocket error: {e}', exc_info=True)
        # Clean up on error
        audio_accumulator.reset_state()
        if user_id:
            manager.disconnect(user_id)
        try:
            await websocket.send_json({
                'type': 'error',
                'error': str(e),
            })
        except Exception:
            pass
    finally:
        # Final cleanup to ensure resources are released
        logger.info('Final cleanup - resetting audio accumulator')
        audio_accumulator.reset_state()
