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
            'intent_type': None,
            'form_data': {},
            'audio_chunks': [],
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
                        # Initial message - just acknowledge
                        logger.info('Voice session initialized')

                        await websocket.send_json({
                            'type': 'init_ack',
                            'message': 'Session initialized, ready to receive audio',
                        })

                    elif message_type == 'stop_recording':
                        # User stopped recording - merge and save audio
                        logger.info(f'Stopping recording. Total chunks received: {len(session_data["audio_chunks"])}')

                        if session_data['audio_chunks']:
                            # Merge all audio chunks
                            merged_audio = b''.join(session_data['audio_chunks'])

                            # Create temp directory if not exists
                            temp_dir = 'temp_audio'
                            os.makedirs(temp_dir, exist_ok=True)

                            # Generate filename with timestamp
                            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f'{temp_dir}/voice_{user_id}_{timestamp}.webm'

                            # Save merged audio
                            with open(filename, 'wb') as f:
                                f.write(merged_audio)

                            logger.info(f'✅ Audio saved: {filename}, size: {len(merged_audio)} bytes')

                            await websocket.send_json({
                                'type': 'recording_stopped',
                                'message': f'Recording saved successfully ({len(merged_audio)} bytes)',
                                'filename': filename,
                                'chunks_count': len(session_data['audio_chunks']),
                            })

                            # Clear chunks after saving
                            session_data['audio_chunks'] = []
                        else:
                            logger.warning('No audio chunks to save')
                            await websocket.send_json({
                                'type': 'error',
                                'error': 'No audio data received',
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
