from __future__ import annotations

import json
from typing import Any
from typing import Dict

from api.dependencies import get_audio_stream_accumulator
from api.dependencies import get_infra_manager_ws
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
from infra.infra_manager import InfrastructureManager
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
        logger.debug(f'User {user_id} connected to voice input')

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.debug(f'User {user_id} disconnected from voice input')

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = VoiceConnectionManager()


def _normalize_intent_type(intent_type: str) -> str:
    return intent_type.upper()


async def _enrich_transfer_parameters(
    parameters: Dict[str, Any],
    user_id: int,
    websocket: WebSocket,
    contact_repo,
    account_repo,
) -> None:
    """
    Enrich transfer parameters by resolving recipient name to account number.
    Modifies parameters dict in-place.

    Search order:
    1. User's contacts (danh bạ đã lưu)
    2. Other users' accounts (tài khoản trong hệ thống)

    If user said "chuyển cho mẹ", this will:
    1. Look up contact named "mẹ"
    2. If not found in contacts, search in other users' accounts by name
    3. Add recipient_account_number to parameters
    4. Keep recipient_name for display

    If multiple matches found, send error to client.
    """
    # Check if we need to resolve recipient
    recipient_name = parameters.get('recipient_name')
    recipient = parameters.get('recipient')

    # Skip if account number already provided
    if parameters.get('recipient_account_number'):
        logger.debug('Account number already provided, skipping enrichment')
        return

    # Determine what to resolve
    name_to_resolve = None
    if recipient_name:
        name_to_resolve = recipient_name
    elif recipient and not recipient.isdigit():
        # recipient is a name, not account number
        name_to_resolve = recipient

    if not name_to_resolve:
        logger.debug('No name to resolve')
        return

    try:
        # === Step 1: Search in user's contacts ===
        user_contacts = await contact_repo.get_by_user_id(user_id)

        # Search by exact match (case-insensitive)
        matching_contacts = [
            c for c in user_contacts
            if c.contact_name.lower() == name_to_resolve.lower()
        ]

        if len(matching_contacts) == 1:
            contact = matching_contacts[0]
            # Found exactly one match in contacts - enrich parameters
            parameters['recipient_account_number'] = contact.account_number
            parameters['recipient_name'] = contact.contact_name
            logger.debug(f'✅ Enriched from CONTACTS: {contact.contact_name} → {contact.account_number}')
            return
        elif len(matching_contacts) > 1:
            # Multiple matches in contacts - send error to client
            match_list = [
                {
                    'name': c.contact_name,
                    'account_number': c.account_number,
                    'bank': c.bank_name or 'Unknown',
                }
                for c in matching_contacts
            ]

            await websocket.send_json({
                'type': 'clarification_needed',
                'field': 'recipient',
                'message': f'Tìm thấy {len(matching_contacts)} người có tên "{name_to_resolve}" trong danh bạ',
                'matches': match_list,
            })
            logger.warning(f'Multiple contacts found for "{name_to_resolve}"')
            return

        # Try partial match in contacts
        partial_matches = [
            c for c in user_contacts
            if name_to_resolve.lower() in c.contact_name.lower()
        ]

        if len(partial_matches) == 1:
            contact = partial_matches[0]
            parameters['recipient_account_number'] = contact.account_number
            parameters['recipient_name'] = contact.contact_name
            logger.debug(f'✅ Enriched from CONTACTS (partial): {contact.contact_name} → {contact.account_number}')
            return
        elif len(partial_matches) > 1:
            match_list = [
                {
                    'name': c.contact_name,
                    'account_number': c.account_number,
                    'bank': c.bank_name or 'Unknown',
                }
                for c in partial_matches
            ]

            await websocket.send_json({
                'type': 'clarification_needed',
                'field': 'recipient',
                'message': f'Tìm thấy {len(partial_matches)} người có tên giống "{name_to_resolve}" trong danh bạ',
                'matches': match_list,
            })
            logger.warning(f'Multiple partial matches in contacts for "{name_to_resolve}"')
            return

        # === Step 2: Search in other users' accounts ===
        logger.debug(f'No contact found for "{name_to_resolve}", searching in other accounts...')

        other_accounts = await account_repo.get_other_users_accounts(exclude_user_id=user_id)

        # Search by exact match in account_name or user's full_name
        matching_accounts = [
            (account, user) for account, user in other_accounts
            if (
                account.account_name.lower() == name_to_resolve.lower() or
                user.full_name.lower() == name_to_resolve.lower()
            )
        ]

        if len(matching_accounts) == 1:
            account, user = matching_accounts[0]
            parameters['recipient_account_number'] = account.account_number
            parameters['recipient_name'] = user.full_name  # Only user's full name
            logger.info(f'✅ Enriched from OTHER ACCOUNTS: {user.full_name} → {account.account_number}')
            return
        elif len(matching_accounts) > 1:
            match_list = [
                {
                    'name': f'{user.full_name} ({account.account_name})',
                    'account_number': account.account_number,
                    'bank': 'Internal',
                }
                for account, user in matching_accounts
            ]

            await websocket.send_json({
                'type': 'clarification_needed',
                'field': 'recipient',
                'message': f'Tìm thấy {len(matching_accounts)} tài khoản có tên "{name_to_resolve}"',
                'matches': match_list,
            })
            logger.warning(f'Multiple other accounts found for "{name_to_resolve}"')
            return

        # Try partial match in other accounts
        partial_account_matches = [
            (account, user) for account, user in other_accounts
            if (
                name_to_resolve.lower() in account.account_name.lower() or
                name_to_resolve.lower() in user.full_name.lower()
            )
        ]

        if len(partial_account_matches) == 1:
            account, user = partial_account_matches[0]
            parameters['recipient_account_number'] = account.account_number
            parameters['recipient_name'] = user.full_name  # Only user's full name
            logger.debug(f'✅ Enriched from OTHER ACCOUNTS (partial): {user.full_name} → {account.account_number}')
            return
        elif len(partial_account_matches) > 1:
            match_list = [
                {
                    'name': f'{user.full_name} ({account.account_name})',
                    'account_number': account.account_number,
                    'bank': 'Internal',
                }
                for account, user in partial_account_matches
            ]

            await websocket.send_json({
                'type': 'clarification_needed',
                'field': 'recipient',
                'message': f'Tìm thấy {len(partial_account_matches)} tài khoản có tên giống "{name_to_resolve}"',
                'matches': match_list,
            })
            logger.warning(f'Multiple partial matches in other accounts for "{name_to_resolve}"')
            return

        # No matches found anywhere
        logger.warning(f'❌ No contact or account found for "{name_to_resolve}"')

    except Exception as e:
        logger.error(f'Error enriching transfer parameters: {e}', exc_info=True)


@router.websocket('/stream')
async def voice_stream(
    websocket: WebSocket,
    token: str,
    audio_accumulator: AudioStreamAccumulator = Depends(get_audio_stream_accumulator),
    intent_service: IntentUnderstandingService = Depends(get_intent_service_ws),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service_ws),
    infra_manager: InfrastructureManager = Depends(get_infra_manager_ws),
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
            'current_page': None,  # Current page user is on
            'current_dialog': None,  # Current dialog that is open
            'is_recording': False,
        }

        # Start new session in accumulator
        audio_accumulator.start_new_session()

        # Callback for when a segment is processed
        async def on_segment_processed(seg_id: int, text: str):
            """Send intermediate transcription to client"""
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
                        current_page = data.get('current_page')
                        current_dialog = data.get('current_dialog')

                        logger.info(f'🔍 Init message received: intent_type={hint_intent_type}, form_data={form_data}')

                        session_data['hint_intent_type'] = hint_intent_type
                        session_data['form_data'] = form_data
                        session_data['current_page'] = current_page
                        session_data['current_dialog'] = current_dialog
                        session_data['is_recording'] = True

                        logger.info(f'Voice session initialized - page: {current_page}, dialog: {current_dialog}, intent: {hint_intent_type}')

                        await websocket.send_json({
                            'type': 'init_ack',
                            'message': 'Session initialized, ready to receive audio',
                        })

                    elif message_type == 'stop_recording':
                        # User clicked ✓ (Stop & Save) - process the recording
                        session_data['is_recording'] = False

                        try:
                            # HARDCODED FOR TESTING - Comment out Whisper transcription
                            final_text = await audio_accumulator.get_transcription(auto_reset=True)
                            # final_text = "xem tình hình tài chính"

                            logger.debug(f'Transcription: "{final_text}"')

                            if not final_text or not final_text.strip():
                                await websocket.send_json({
                                    'type': 'error',
                                    'error': 'Could not transcribe audio. Please try again.',
                                })
                                continue

                            # Step 3: Intent Understanding
                            # Normalize hint_intent_type from frontend format to backend format
                            hint_intent_type = session_data['hint_intent_type']
                            if hint_intent_type:
                                hint_intent_type = _normalize_intent_type(hint_intent_type)

                            logger.info(f'🔍 Calling extract_intent_and_params with hint_intent_type={hint_intent_type} (original: {session_data["hint_intent_type"]})')
                            intent_result = await intent_service.extract_intent_and_params(
                                text=final_text,
                                form_data=session_data['form_data'],
                                hint_intent_type=hint_intent_type,
                            )

                            intent_type = intent_result['intent_type']
                            parameters = intent_result['parameters']

                            logger.debug(f'Intent extracted: {intent_type} with params: {parameters}')

                            # Step 3.5: Enrich parameters for SEND_MONEY intent
                            # If user provided recipient_name, try to resolve it to account number
                            if intent_type == 'SEND_MONEY':
                                # Get repositories from infra_manager
                                contact_repo = infra_manager.contact_repository
                                account_repo = infra_manager.account_repository

                                await _enrich_transfer_parameters(
                                    parameters=parameters,
                                    user_id=int(user_id),
                                    websocket=websocket,
                                    contact_repo=contact_repo,
                                    account_repo=account_repo,
                                )

                            # Step 4: Check if intent changed
                            # Logic:
                            # - If hint_intent_type is None (user on general page like dashboard)
                            #   → intent_changed = True (always navigate to the target page)
                            # - If hint_intent_type is not None (user on specific form page)
                            #   → intent_changed = True if extracted intent differs from hint
                            #   → intent_changed = False if extracted intent matches hint (stay on same form)
                            # Note: hint_intent_type is already normalized to backend format above
                            if hint_intent_type is None:
                                # User on general page, any intent means navigation needed
                                intent_changed = True
                            else:
                                # User on specific form, check if intent differs
                                intent_changed = (intent_type != hint_intent_type)

                            logger.info(f'🔍 Intent change detection: hint={hint_intent_type}, extracted={intent_type}, changed={intent_changed}')

                            # Step 5: Get plugin to check if needs confirmation
                            from domain.plugins.registry import get_plugin_registry
                            plugin_registry = get_plugin_registry()
                            plugin = plugin_registry.get_plugin(intent_type)

                            needs_confirmation = True  # Default to True for safety
                            if plugin:
                                # Check if plugin requires confirmation for voice input
                                needs_confirmation = plugin.requires_voice_confirmation

                            # Step 6: Determine suggested action based on context
                            suggested_action = 'stay'  # Default action

                            if intent_changed:
                                # User changed intent - suggest navigation or dialog open
                                # For create intents, open dialog
                                if intent_type.startswith('CREATE_'):
                                    suggested_action = 'open_dialog'
                                # For fund operations (deposit/withdraw), open dialog to select fund
                                elif intent_type in ['DEPOSIT_FUND', 'WITHDRAW_FUND', 'DELETE_FUND']:
                                    suggested_action = 'open_dialog'
                                # For bill payment, open dialog to select bill
                                elif intent_type == 'pay_bill':
                                    suggested_action = 'open_dialog'
                                # For view/list intents, navigate to page
                                elif intent_type in ['VIEW_BILLS', 'VIEW_FUNDS', 'VIEW_ACCOUNTS', 'VIEW_TRANSFERS']:
                                    suggested_action = 'navigate'
                                # For query intents (check balance, query finance), navigate
                                elif intent_type in ['CHECK_BALANCE', 'QUERY_FINANCE']:
                                    suggested_action = 'navigate'
                                # For other intents (send_money, etc.), navigate
                                else:
                                    suggested_action = 'navigate'
                            else:
                                # Same intent - just update form or stay
                                if parameters:
                                    suggested_action = 'update_form'
                                else:
                                    suggested_action = 'stay'

                            # Step 7: Prepare response
                            response_data = {
                                'type': 'intent_extracted',
                                'asr_text': final_text,
                                'normalized_text': final_text,
                                'intent_type': intent_type,
                                'parameters': parameters,
                                'intent_changed': intent_changed,
                                'needs_confirmation': needs_confirmation,
                                'action': suggested_action,  # Add suggested action
                            }

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

                        except Exception as e:
                            logger.error(f'Error executing intent: {e}', exc_info=True)
                            await websocket.send_json({
                                'type': 'execution_error',
                                'error': str(e),
                            })

                    elif message_type == 'cancel':
                        # User clicked ✕ (Cancel) - discard everything
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
        logger.debug('WebSocket disconnected - cleaning up resources')
        audio_accumulator.reset_state()
        if user_id:
            manager.disconnect(user_id)
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
        logger.debug('Final cleanup - resetting audio accumulator')
        audio_accumulator.reset_state()
