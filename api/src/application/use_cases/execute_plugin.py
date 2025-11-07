from __future__ import annotations

from domain.entities.execution_result import ExecutionResult
from domain.plugins.registry import get_intent_plugin


async def execute(intent_type: str, **kwargs) -> ExecutionResult:
    """Execute intent plugin based on intent type"""
    plugin = get_intent_plugin(intent_type)

    if not plugin:
        return ExecutionResult(
            success=False,
            message=f'Plugin for intent {intent_type} not found',
            data={'error_type': 'UNKNOWN_INTENT'},
        )

    parameters = kwargs.get('parameters', {})
    context = kwargs.get('context', {})

    return await plugin.execute(parameters, context)
