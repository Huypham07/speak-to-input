"""
Test 2: Extract Missing Params (With hint_intent_type)
Run:
  - python -m pytest tests/intent_classify/test_intent_missing_params.py -v -s
  - or: python tests/intent_classify/test_intent_missing_params.py
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


async def test_extract_missing_params():
    print('\n' + '=' * 60)
    print('  TEST 2: EXTRACT MISSING PARAMS (With hint_intent_type)')
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
        # SEND_MONEY - Missing recipient
        {
            'text': 'Cho mẹ',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000},
            'expected_intent': 'SEND_MONEY',
            'expected_new_params': ['recipient'],
        },
        # SEND_MONEY - Missing amount
        {
            'text': '500 nghìn',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'recipient': 'mẹ'},
            'expected_intent': 'SEND_MONEY',
            'expected_new_params': ['amount'],
        },
        # CREATE_BILL - Missing amount and due_date
        {
            'text': '200 nghìn, hạn ngày 15',
            'hint_intent_type': 'CREATE_BILL',
            'form_data': {'bill_name': 'Tiền điện'},
            'expected_intent': 'CREATE_BILL',
            'expected_new_params': ['amount', 'due_date'],
        },
        # CREATE_FUND - Missing target_amount
        {
            'text': '50 triệu',
            'hint_intent_type': 'CREATE_FUND',
            'form_data': {
                'fund_name': 'Mua xe',
                'target_date': '2025-12-31',
            },
            'expected_intent': 'CREATE_FUND',
            'expected_new_params': ['target_amount'],
        },
        # English cases
        {
            'text': 'To mom',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000},
            'expected_intent': 'SEND_MONEY',
            'expected_new_params': ['recipient'],
        },
        {
            'text': '500 thousand',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'recipient': 'mom'},
            'expected_intent': 'SEND_MONEY',
            'expected_new_params': ['amount'],
        },
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        hint_intent = test_case['hint_intent_type']
        form_data = test_case['form_data']
        expected_intent = test_case['expected_intent']
        expected_new_params = test_case['expected_new_params']

        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"📝 Input: '{text}'")
        print(f"🎯 Hint Intent: {hint_intent}")
        print(f"📋 Form Data: {form_data}")
        print(f"🎯 Expected Intent: {expected_intent}")
        print(f"🎯 Expected New Params: {expected_new_params}")

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
            form_data_preserved = all(
                form_data.get(k) == parameters.get(k)
                for k in form_data.keys()
                if k in parameters
            )
            new_params_extracted = all(
                param in parameters for param in expected_new_params
            )

            print(f"✅ Intent: {actual_intent}")
            print(f"📊 Confidence: {confidence:.2%}")
            print(f"📦 All Parameters: {parameters}")
            print(f"✅ Form data preserved: {form_data_preserved}")
            print(f"✅ New params extracted: {new_params_extracted}")

            if is_intent_correct and form_data_preserved and new_params_extracted:
                print(f"   ✅ PASS")
                passed += 1
            else:
                print(f"   ❌ FAIL")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ Passed: {passed}/{len(test_cases)}")


if __name__ == '__main__':
    asyncio.run(test_extract_missing_params())
