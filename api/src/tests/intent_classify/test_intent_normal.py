"""
Test 1: Normal Classification (No hint_intent_type)
Run:
  - python -m pytest tests/intent_classify/test_intent_normal.py -v -s
  - or: python tests/intent_classify/test_intent_normal.py
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


async def test_normal_classification():
    print('\n' + '=' * 60)
    print('  TEST 1: NORMAL CLASSIFICATION (No hint_intent_type)')
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
        # Vietnamese
        {
            'text': 'Chuyển 500 nghìn cho mẹ',
            'expected_intent': 'SEND_MONEY',
            'expected_params': ['amount', 'recipient'],
        },
        {
            'text': 'Tạo hóa đơn tiền điện 200 nghìn, hạn ngày 15',
            'expected_intent': 'CREATE_BILL',
            'expected_params': ['bill_name', 'amount', 'due_date'],
        },
        {
            'text': 'Xem số dư tài khoản',
            'expected_intent': 'CHECK_BALANCE',
            'expected_params': [],
        },
        # English
        {
            'text': 'Transfer 500 thousand to mom',
            'expected_intent': 'SEND_MONEY',
            'expected_params': ['amount', 'recipient'],
        },
        {
            'text': 'Create an electricity bill for 200 thousand, due on the 15th',
            'expected_intent': 'CREATE_BILL',
            'expected_params': ['bill_name', 'amount', 'due_date'],
        },
        {
            'text': 'Check account balance',
            'expected_intent': 'CHECK_BALANCE',
            'expected_params': [],
        },
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        expected_intent = test_case['expected_intent']
        expected_params = test_case['expected_params']

        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"📝 Input: '{text}'")
        print(f"🎯 Expected Intent: {expected_intent}")

        try:
            result = await intent_service.extract_intent_and_params(
                text=text,
                form_data=None,
                hint_intent_type=None,
            )

            actual_intent = result['intent_type']
            parameters = result['parameters']
            confidence = result['confidence']

            is_correct = actual_intent == expected_intent
            status = '✅ PASS' if is_correct else '❌ FAIL'

            print(f"🤖 Actual Intent: {actual_intent}")
            print(f"📊 Confidence: {confidence:.2%}")
            print(f"📦 Parameters: {parameters}")
            
            if expected_params:
                params_present = all(param in parameters for param in expected_params)
                print(f"✅ Expected params present: {params_present} -> {expected_params}")
            
            print(f"   {status}")

            if is_correct:
                passed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ Passed: {passed}/{len(test_cases)}")


if __name__ == '__main__':
    asyncio.run(test_normal_classification())
