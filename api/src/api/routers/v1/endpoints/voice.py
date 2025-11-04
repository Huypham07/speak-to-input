from __future__ import annotations

from typing import Any
from typing import Dict

from api.dependencies import get_intent_service
from api.dependencies import get_orchestration_service
from api.dependencies import get_voice_service
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
    voice_service: VoiceService = Depends(get_voice_service),
    intent_service: IntentUnderstandingService = Depends(get_intent_service),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
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
            # Receive data from frontend
            data = await websocket.receive_json()
            message_type = data.get('type')

            if message_type == 'init':
                # Initial message with form data and intent (optional)
                session_data['intent_type'] = data.get('intent_type')
                session_data['form_data'] = data.get('form_data', {})

                logger.info(f'Voice session initialized: intent={session_data["intent_type"]}, form_data={session_data["form_data"]}')

                await websocket.send_json({
                    'type': 'init_ack',
                    'message': 'Session initialized, ready to receive audio',
                })

            elif message_type == 'audio_chunk':
                # Receive audio chunk
                audio_data = data.get('audio')

                # Store audio chunk
                session_data['audio_chunks'].append(audio_data)

                # TODO: Process audio with Voice Service (Whisper)
                # For now, just acknowledge
                logger.debug(f'Received audio chunk: {len(audio_data) if audio_data else 0} bytes')

                await websocket.send_json({
                    'type': 'audio_ack',
                    'message': 'Audio chunk received',
                })

            elif message_type == 'process_voice':
                # Process all collected audio chunks
                logger.info('Processing voice input...')

                # Step 1: Voice Service - Speech to text (PLACEHOLDER)
                # TODO: Implement voice_service.transcribe(audio_chunks)
                transcribed_text = 'placeholder text'  # Placeholder

                logger.info(f'Transcribed text: {transcribed_text}')

                # Step 2: Intent Service - Extract intent and parameters
                try:
                    intent_result = await intent_service.extract_intent_and_params(
                        text=transcribed_text,
                        form_data=session_data['form_data'],
                        hint_intent_type=session_data.get('intent_type'),
                    )

                    logger.info(f'Intent extracted: {intent_result}')

                    # Send extracted params back to frontend for review
                    await websocket.send_json({
                        'type': 'intent_extracted',
                        'intent_type': intent_result['intent_type'],
                        'parameters': intent_result['parameters'],
                        'confidence': intent_result.get('confidence', 0.0),
                    })

                except Exception as e:
                    logger.error(f'Intent extraction error: {e}')
                    await websocket.send_json({
                        'type': 'error',
                        'error': f'Failed to understand voice input: {str(e)}',
                    })

                # Clear audio chunks
                session_data['audio_chunks'] = []

            elif message_type == 'execute':
                # Execute intent with parameters (from voice or form)
                intent_type = data.get('intent_type')
                parameters = data.get('parameters', {})

                logger.info(f'Executing intent: {intent_type} with parameters: {parameters}')

                # Step 3: Orchestration Service - Execute
                result = await orchestration_service.execute_intent(
                    intent_type=intent_type,
                    parameters=parameters,
                    user_id=int(user_id),
                )

                if result.success:
                    # Check if needs confirmation
                    needs_confirmation = data.get('needs_confirmation', False)

                    if needs_confirmation:
                        await websocket.send_json({
                            'type': 'confirmation_required',
                            'data': result.data,
                            'message': result.message or 'Please confirm',
                        })
                    else:
                        await websocket.send_json({
                            'type': 'execution_success',
                            'data': result.data,
                            'message': result.message or 'Success',
                        })
                else:
                    await websocket.send_json({
                        'type': 'execution_error',
                        'error': result.message,
                        'error_type': result.data.get('error_type', 'UNKNOWN'),
                        'data': result.data,
                    })

            elif message_type == 'confirm':
                # User confirmed action
                intent_type = data.get('intent_type')
                parameters = data.get('parameters', {})

                logger.info(f'User confirmed execution: {intent_type}')

                result = await orchestration_service.execute_intent(
                    intent_type=intent_type,
                    parameters=parameters,
                    user_id=int(user_id),
                )

                if result.success:
                    await websocket.send_json({
                        'type': 'execution_success',
                        'data': result.data,
                        'message': result.message or 'Success',
                    })
                else:
                    await websocket.send_json({
                        'type': 'execution_error',
                        'error': result.message,
                        'error_type': result.data.get('error_type', 'UNKNOWN'),
                    })

            elif message_type == 'ping':
                await websocket.send_json({'type': 'pong'})

            else:
                logger.warning(f'Unknown message type: {message_type}')

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
