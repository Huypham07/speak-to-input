from __future__ import annotations

import datetime
import json
import os
from typing import Any
from typing import Dict

from api.dependencies import get_intent_service_ws
from api.dependencies import get_orchestration_service_ws
from api.dependencies import get_voice_service_ws
from api.helpers.jwt_auth import verify_token
from application.services.intent_service import IntentUnderstandingService
from application.services.orchestration_service import OrchestrationService
from application.services.voice_service import VoiceService
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
    voice_service: VoiceService = Depends(get_voice_service_ws),
    intent_service: IntentUnderstandingService = Depends(get_intent_service_ws),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service_ws),
):
    """
    WebSocket endpoint for voice input streaming.
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
            'audio_chunks': [],
            'is_recording': False,
        }

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
                        logger.info(f'Processing recording. Total chunks: {len(session_data["audio_chunks"])}')

                        session_data['is_recording'] = False

                        if not session_data['audio_chunks']:
                            logger.warning('No audio chunks to process')
                            await websocket.send_json({
                                'type': 'error',
                                'error': 'No audio data received',
                            })
                            continue

                        try:
                            # Step 1: Merge audio chunks
                            merged_audio = b''.join(session_data['audio_chunks'])
                            logger.info(f'✅ Merged audio: {len(merged_audio)} bytes from {len(session_data["audio_chunks"])} chunks')

                            # Step 2: Speech-to-Text + Normalization
                            logger.info('🎤 Starting STT...')
                            asr_text, normalized_text = await voice_service.process(merged_audio)

                            logger.info(f'📝 ASR result: "{asr_text}"')
                            logger.info(f'🔧 Normalized: "{normalized_text}"')

                            if not normalized_text or not normalized_text.strip():
                                await websocket.send_json({
                                    'type': 'error',
                                    'error': 'Could not transcribe audio. Please try again.',
                                })
                                continue

                            # Step 3: Intent Understanding
                            logger.info('🧠 Extracting intent...')
                            intent_result = await intent_service.extract_intent_and_params(
                                text=normalized_text,
                                form_data=session_data['form_data'],
                                hint_intent_type=session_data['hint_intent_type'],
                            )

                            intent_type = intent_result['intent_type']
                            parameters = intent_result['parameters']

                            logger.info(f'✨ Intent: {intent_type}')
                            logger.info(f'📋 Parameters: {parameters}')

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
                                'asr_text': asr_text,
                                'normalized_text': normalized_text,
                                'intent_type': intent_type,
                                'parameters': parameters,
                                'intent_changed': intent_changed,
                                'needs_confirmation': needs_confirmation,
                            }

                            logger.info(f'📤 Sending response: intent_changed={intent_changed}, needs_confirmation={needs_confirmation}')
                            await websocket.send_json(response_data)

                            # Clear audio chunks
                            session_data['audio_chunks'] = []

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

                        logger.info(f'🚀 Executing confirmed intent: {intent_type}')
                        logger.info(f'   Parameters: {parameters}')

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
                        session_data['audio_chunks'] = []
                        session_data['is_recording'] = False

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
                    session_data['audio_chunks'].append(audio_chunk)

                    chunk_size = len(audio_chunk)
                    total_chunks = len(session_data['audio_chunks'])

                    logger.debug(f'>>> Audio chunk received: {chunk_size} bytes (total chunks: {total_chunks})')

                    # Send acknowledgment
                    await websocket.send_json({
                        'type': 'audio_chunk_ack',
                        'chunk_number': total_chunks,
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
        if user_id:
            manager.disconnect(user_id)
        logger.info('WebSocket disconnected')
    except Exception as e:
        logger.error(f'WebSocket error: {e}', exc_info=True)
        if user_id:
            manager.disconnect(user_id)
        try:
            await websocket.send_json({
                'type': 'error',
                'error': str(e),
            })
        except Exception:
            pass
