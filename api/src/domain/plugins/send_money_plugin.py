from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from domain.entities.business_state import BusinessState
from domain.entities.capability import Capability
from domain.entities.execution_result import ExecutionResult
from domain.entities.field_validation import FieldValidation
from domain.entities.field_validation import ValidationResult
from domain.plugins.base_intent_plugin import IntentPlugin
from domain.value_objects.capability_type import CapabilityType
from domain.value_objects.field_status import FieldStatus


class SendMoneyPlugin(IntentPlugin):
    """Plugin for SEND_MONEY intent"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return 'SEND_MONEY'

    @property
    def display_name(self) -> str:
        return 'Chuyển tiền'

    @property
    def description(self) -> str:
        return 'Transfer money to another account or contact'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'required': ['amount', 'recipient'],
            'properties': {
                'amount': {
                    'type': 'number',
                    'minimum': 10000,
                    'maximum': 50000000,
                    'description': 'Transfer amount in VND',
                },
                'recipient': {
                    'type': 'string',
                    'description': 'Recipient identifier (contact ID or account number)',
                },
                'message': {
                    'type': 'string',
                    'maxLength': 200,
                    'description': 'Transfer message',
                },
            },
        }

    # ========== Validation ==========

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate transfer parameters"""
        results = []

        # Validate amount
        amount = parameters.get('amount')
        if not amount:
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        elif amount < 10000 or amount > 50000000:
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.INVALID,
                    value=amount,
                    confidence=0.0,
                    error_message='Số tiền phải từ 10,000 đến 50,000,000 VND',
                ),
            )
        else:
            # TODO: Check user balance
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.VALID,
                    value=amount,
                    confidence=1.0,
                ),
            )

        # Validate recipient
        recipient = parameters.get('recipient')
        if not recipient:
            results.append(
                FieldValidation(
                    field_name='recipient',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        else:
            # TODO: Resolve recipient (check if ambiguous)
            # For now, assume valid
            results.append(
                FieldValidation(
                    field_name='recipient',
                    status=FieldStatus.VALID,
                    value=recipient,
                    confidence=1.0,
                ),
            )

        # Determine overall validity
        is_valid = all(r.status == FieldStatus.VALID for r in results)
        missing = [r for r in results if r.status == FieldStatus.MISSING]
        invalid = [r for r in results if r.status == FieldStatus.INVALID]
        ambiguous = [r for r in results if r.status == FieldStatus.AMBIGUOUS]

        return ValidationResult(
            is_valid=is_valid,
            field_results=results,
            missing_fields=missing,
            invalid_fields=invalid,
            ambiguous_fields=ambiguous,
        )

    # ========== Capability Resolution ==========

    def resolve_capabilities(
        self,
        parameters: Dict[str, Any],
        validation_result: ValidationResult,
        state: BusinessState,
    ) -> List[Capability]:
        """Resolve capabilities based on validation"""
        capabilities = []

        # If amount is missing, request it
        if validation_result.missing_fields:
            for field in validation_result.missing_fields:
                if field.field_name == 'amount':
                    capabilities.append(
                        Capability(
                            capability_type=CapabilityType.REQUEST_FIELD,
                            priority=1,
                            data={
                                'field': 'amount',
                                'message': 'Bạn muốn chuyển bao nhiêu?',
                            },
                        ),
                    )
                elif field.field_name == 'recipient':
                    capabilities.append(
                        Capability(
                            capability_type=CapabilityType.REQUEST_FIELD,
                            priority=2,
                            data={
                                'field': 'recipient',
                                'message': 'Chuyển cho ai?',
                            },
                        ),
                    )

        return capabilities

    # ========== State Machine ==========

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute money transfer"""
        # TODO: Implement actual transfer logic
        # - Call banking API
        # - Handle errors
        # - Return transaction ID

        return ExecutionResult(
            success=True,
            message=f"Chuyển {parameters['amount']:,} VND thành công",
            data={
                'amount': parameters['amount'],
                'recipient': parameters['recipient'],
            },
        )
