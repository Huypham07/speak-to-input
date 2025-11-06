"""
Test 4: All Params Provided (No missing fields)
Run:
  - python -m pytest tests/intent_classify/test_intent_all_params_provided.py -v -s
  - or: python tests/intent_classify/test_intent_all_params_provided.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from application.services.intent_service import IntentUnderstandingService
from domain.plugins.registry import IntentPluginRegistry
from infra.llm.llm_service import LLMService
from shared.settings import Settings


async def test_all_params_provided():
    print('\n' + '=' * 60)
    print('  TEST 4: ALL PARAMS PROVIDED (No missing fields)')
    print('=' * 60 + '\n')

    settings = Settings()
    llm_service = LLMService(settings)
    plugin_registry = IntentPluginRegistry()
    plugin_registry.discover_plugins()

    intent_service = IntentUnderstandingService(
        settings=settings,
        llm_service=llm_service,
        plugin_registry=plugin_registry,
    )

    test_cases = [
        # SEND_MONEY - All params provided
        {
            'text': 'Ok được rồi',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {
                'amount': 500000,
                'recipient': 'mẹ',
            },
            'expected_intent': 'SEND_MONEY',
        },
        # CREATE_BILL - All params provided
        {
            'text': 'Xác nhận',
            'hint_intent_type': 'CREATE_BILL',
            'form_data': {
                'bill_name': 'Tiền điện',
                'amount': 200000,
                'due_date': '2024-12-15',
            },
            'expected_intent': 'CREATE_BILL',
        },
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        hint_intent = test_case['hint_intent_type']
        form_data = test_case['form_data']
        expected_intent = test_case['expected_intent']

        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"📝 Input: '{text}'")
        print(f"🎯 Hint Intent: {hint_intent}")
        print(f"📋 Form Data: {form_data}")

        try:
            result = await intent_service.extract_intent_and_params(
                text=text,
                form_data=form_data,
                hint_intent_type=hint_intent,
            )

            actual_intent = result['intent_type']
            parameters = result['parameters']
            confidence = result['confidence']

            is_intent_correct = actual_intent == expected_intent
            params_match = all(form_data.get(k) == parameters.get(k) for k in form_data.keys())

            status = '✅ PASS' if (is_intent_correct and params_match) else '❌ FAIL'

            print(f"🤖 Actual Intent: {actual_intent}")
            print(f"📊 Confidence: {confidence:.2%}")
            print(f"📦 Parameters: {parameters}")
            print(f"✅ Intent correct: {is_intent_correct}")
            print(f"✅ Params match form_data: {params_match}")
            print(f"   {status}")

            if is_intent_correct and params_match:
                passed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ Passed: {passed}/{len(test_cases)}")


if __name__ == '__main__':
    asyncio.run(test_all_params_provided())
