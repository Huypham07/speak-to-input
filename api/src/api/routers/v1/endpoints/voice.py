from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from typing import Dict

from domain.value_objects import StateType
from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from shared.logging import get_logger

logger = get_logger(__name__)

voice_router = APIRouter(prefix='/voice', tags=['voice'])


# ============ Streaming ============

@voice_router.websocket('/stream')
async def process_voice_stream(
    websocket: WebSocket,
):
    """
    WebSocket endpoint for streaming voice processing.

    Push-to-talk flow:
    1. User presses mic button -> sends 'recording_start'
    2. User speaks -> sends continuous 'audio_chunk' messages
    3. User presses mic button -> sends 'recording_end'
    4. Server processes complete audio through pipeline
    5. Server returns result based on conversation state

    Message Types (Client -> Server):
    - init: Initialize session
    - recording_start: User starts speaking
    - audio_chunk: Audio data chunk (base64)
    - recording_end: User finished speaking

    Message Types (Server -> Client):
    - ready: Session initialized
    - recording_started: Recording acknowledged
    - partial_transcript: Real-time ASR result
    - final_transcript: Complete ASR result
    - intent_classified: Intent detection result
    - need_clarification: Request missing information
    - need_confirmation: Request user confirmation
    - execution_result: Final execution result
    - error: Error occurred
    """
    await websocket.accept()

    # Get use case instance (without dependency injection in WebSocket)
    from api.dependencies import get_settings
    from api.dependencies import get_voice_service
    from api.dependencies import get_intent_service
    from api.dependencies import get_state_machine_service

    # Create mock request to get settings
    class MockRequest:
        class State:
            settings = None
            infra_manager = None
        app = type('obj', (object,), {'state': State()})()

    # You'll need to pass actual settings here - this is a placeholder
    # In production, consider using a different pattern for WebSocket dependencies

    # Session state - persistent during WebSocket connection
    session_state: Dict[str, Any] = {
        'session_id': None,
        'user_id': None,
        'conversation_state': StateType.INITIAL,
        'current_action': None,
        'accumulated_data': {},
        'context': [],
        # Recording state
        'is_recording': False,
        'audio_buffer': [],
    }

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get('type')

            # ============ INITIALIZE SESSION ============
            if message_type == 'init':
                session_state['session_id'] = data.get('session_id') or str(uuid.uuid4())
                session_state['user_id'] = data.get('user_id', 'unknown')

                await websocket.send_json({
                    'type': 'ready',
                    'session_id': session_state['session_id'],
                })
                logger.info(f"Session initialized: {session_state['session_id']}")

            # ============ RECORDING START ============
            elif message_type == 'recording_start':
                session_state['is_recording'] = True
                session_state['audio_buffer'] = []

                await websocket.send_json({
                    'type': 'recording_started',
                    'current_state': session_state['conversation_state'],
                })
                logger.info(f"Recording started: {session_state['session_id']}")

            # ============ AUDIO CHUNK ============
            elif message_type == 'audio_chunk':
                if not session_state['is_recording']:
                    continue

                audio_chunk = data.get('data')
                session_state['audio_buffer'].append(audio_chunk)

                # TODO: Stream to ASR for partial transcription
                # For now, just acknowledge receipt
                # partial_text = await stream_asr(audio_chunk)
                partial_text = ''  # Placeholder

                if partial_text:
                    await websocket.send_json({
                        'type': 'partial_transcript',
                        'text': partial_text,
                    })

            # ============ RECORDING END - Process Complete Audio ============
            elif message_type == 'recording_end':
                session_state['is_recording'] = False

                if not session_state['audio_buffer']:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'No audio data received',
                    })
                    continue

                # Process the complete audio
                await process_turn(
                    session_state=session_state,
                    websocket=websocket,
                )

                # Clear audio buffer
                session_state['audio_buffer'] = []
                logger.info(f"Recording processed: {session_state['session_id']}")

            else:
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_state.get('session_id')}")
    except Exception as e:
        logger.error(f'Error in WebSocket: {e}', exc_info=True)
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e),
            })
        except Exception:
            pass


async def process_turn(
    session_state: Dict[str, Any],
    websocket: WebSocket,
):
    """
    Process one conversational turn (one press-to-talk cycle).

    This function orchestrates the complete pipeline based on current conversation state:
    - INITIAL/COMPLETED/FAILED/CANCELLED: New intent classification
    - AWAITING_CLARIFICATION: Extract missing data
    - AWAITING_CONFIRMATION: Parse confirmation response
    """
    # TODO: Inject services properly (voice_service, intent_service, state_machine_service)

    # Merge audio chunks
    # complete_audio = ''.join(session_state['audio_buffer'])

    # ============ ASR Processing ============
    try:
        # asr_text, normalized, confidence = await voice_service.process(complete_audio)
        final_text = ''  # Placeholder

        await websocket.send_json({
            'type': 'final_transcript',
            'text': final_text,
        })

    except Exception as e:
        logger.error(f'ASR error: {e}', exc_info=True)
        await websocket.send_json({
            'type': 'error',
            'message': f'ASR processing failed: {str(e)}',
        })
        return

    # ============ Process Based on Conversation State ============
    current_state = session_state['conversation_state']

    if current_state in [StateType.INITIAL, StateType.COMPLETED, StateType.FAILED, StateType.CANCELLED]:
        await handle_new_intent(final_text, session_state, websocket)

    elif current_state == StateType.AWAITING_CLARIFICATION:
        await handle_clarification(final_text, session_state, websocket)

    elif current_state == StateType.AWAITING_CONFIRMATION:
        await handle_confirmation(final_text, session_state, websocket)

    else:
        await websocket.send_json({
            'type': 'error',
            'message': f'Invalid conversation state: {current_state}',
        })


async def handle_new_intent(
    text: str,
    session_state: Dict[str, Any],
    websocket: WebSocket,
):
    """
    Handle new intent classification and processing.

    Flow:
    1. Classify intent
    2. Execute pipeline (validation, data extraction)
    3. Determine next state (clarification/confirmation/execute)
    4. Send appropriate response to client
    """
    # TODO: Call intent_service.process(text, context)
    intent_result: Dict[str, Any] = {}  # Placeholder

    await websocket.send_json({
        'type': 'intent_classified',
        'intent': intent_result.get('intent', 'unknown'),
        'confidence': intent_result.get('confidence', 0.0),
    })

    # Add to context
    session_state['context'].append({
        'turn': len(session_state['context']) + 1,
        'user_input': text,
        'intent': intent_result.get('intent', 'unknown'),
        'timestamp': datetime.now().isoformat(),
    })

    # TODO: Execute pipeline through use_case or state_machine
    # result = await execute_pipeline(intent_result, text, session_state)

    # TODO: Based on result, determine next state and response
    # For now, placeholder response
    pass


async def handle_clarification(
    text: str,
    session_state: Dict[str, Any],
    websocket: WebSocket,
):
    """
    Handle user providing missing information.

    Flow:
    1. Check if user is switching to a new intent
    2. Extract missing data from user's response
    3. Validate if all required data is now complete
    4. Move to confirmation or ask for more data
    """
    # TODO: Check if intent changed
    # is_new_intent = await intent_service.check_intent_change(text, current_intent)
    # if is_new_intent: handle intent conflict

    # TODO: Extract clarification data
    # extracted = await intent_service.extract_clarification_data(
    #     text,
    #     session_state['current_action']['missing_fields'],
    #     session_state['accumulated_data']
    # )
    # session_state['accumulated_data'].update(extracted)

    # Add to context
    session_state['context'].append({
        'turn': len(session_state['context']) + 1,
        'user_input': text,
        'type': 'clarification',
        'timestamp': datetime.now().isoformat(),
    })

    # TODO: Validate completeness
    # validation = await validate_action_data(session_state['current_action'], session_state['accumulated_data'])
    # if validation['is_complete']:
    #     move to confirmation
    # else:
    #     ask for more data
    pass


async def handle_confirmation(
    text: str,
    session_state: Dict[str, Any],
    websocket: WebSocket,
):
    """
    Handle user confirmation or cancellation.

    Flow:
    1. Parse user's response (confirm/cancel/unclear)
    2. If confirmed: execute action and return capabilities
    3. If cancelled: reset state
    4. If unclear: ask again
    """
    # Add to context
    session_state['context'].append({
        'turn': len(session_state['context']) + 1,
        'user_input': text,
        'type': 'confirmation',
        'timestamp': datetime.now().isoformat(),
    })

    # TODO: Parse confirmation
    # confirmation = await intent_service.parse_confirmation(text)

    # TODO: Based on confirmation['intent']:
    # - 'confirm': execute action via plugin and return capabilities
    # - 'cancel': reset state and inform user
    # - 'unclear': ask for clarification
    pass
