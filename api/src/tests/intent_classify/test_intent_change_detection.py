"""
Test 3: Intent Change Detection
Run:
  - python -m pytest tests/intent_classify/test_intent_change_detection.py -v -s
  - or: python tests/intent_classify/test_intent_change_detection.py
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


async def test_intent_change_detection():
    print('\n' + '=' * 60)
    print('  TEST 3: INTENT CHANGE DETECTION')
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
        # Vietnamese - User changes from SEND_MONEY to CHECK_BALANCE
        {
            'text': 'Thôi để sau, xem số dư đi',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000},
            'expected_intent': 'CHECK_BALANCE',
            'should_change': True,
        },
        # Vietnamese - User continues with SEND_MONEY
        {
            'text': 'Cho mẹ',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000},
            'expected_intent': 'SEND_MONEY',
            'should_change': False,
        },
        # Vietnamese - User changes from CREATE_BILL to CREATE_FUND
        {
            'text': 'Thôi, tạo quỹ tiết kiệm mua xe 50 triệu',
            'hint_intent_type': 'CREATE_BILL',
            'form_data': {'bill_name': 'Tiền điện'},
            'expected_intent': 'CREATE_FUND',
            'should_change': True,
        },
        # English - User changes intent
        {
            'text': 'Actually, check my balance instead',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000},
            'expected_intent': 'CHECK_BALANCE',
            'should_change': True,
        },
        # English - User continues
        {
            'text': 'To mom',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000},
            'expected_intent': 'SEND_MONEY',
            'should_change': False,
        },
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        hint_intent = test_case['hint_intent_type']
        form_data = test_case['form_data']
        expected_intent = test_case['expected_intent']
        should_change = test_case['should_change']

        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"📝 Input: '{text}'")
        print(f"🎯 Hint Intent: {hint_intent}")
        print(f"📋 Form Data: {form_data}")
        print(f"🎯 Expected Intent: {expected_intent}")
        print(f"🔄 Should Change: {should_change}")

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
            actually_changed = actual_intent != hint_intent
            change_detected_correctly = (actually_changed == should_change)

            status = '✅ PASS' if (is_intent_correct and change_detected_correctly) else '❌ FAIL'

            print(f"🤖 Actual Intent: {actual_intent}")
            print(f"📊 Confidence: {confidence:.2%}")
            print(f"📦 Parameters: {parameters}")
            print(f"✅ Intent correct: {is_intent_correct}")
            print(f"✅ Change detected correctly: {change_detected_correctly}")
            print(f"   {status}")

            if is_intent_correct and change_detected_correctly:
                passed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ Passed: {passed}/{len(test_cases)}")


if __name__ == '__main__':
    asyncio.run(test_intent_change_detection())
