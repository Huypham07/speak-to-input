"""
Test 2.5: Update Existing Params (User corrects/updates previous params)
Run:
  - python -m pytest tests/intent_classify/test_intent_update_existing.py -v -s
  - or: python tests/intent_classify/test_intent_update_existing.py
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


async def test_update_existing_params():
    print('\n' + '=' * 60)
    print('  TEST 2.5: UPDATE EXISTING PARAMS (Sửa lại param cũ)')
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
        # Vietnamese - User sửa amount từ 500000 thành 1 triệu
        {
            'text': 'Không, 1 triệu nhé',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000, 'recipient': 'mẹ'},
            'expected_intent': 'SEND_MONEY',
            'expected_updated_params': {'amount': 1000000},
            'expected_preserved_params': {'recipient': 'mẹ'},
        },
        # Vietnamese - User sửa recipient
        {
            'text': 'Không, cho bố',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000, 'recipient': 'mẹ'},
            'expected_intent': 'SEND_MONEY',
            'expected_updated_params': {'recipient': 'bố'},
            'expected_preserved_params': {'amount': 500000},
        },
        # Vietnamese - User sửa amount và recipient
        {
            'text': '2 triệu cho chị',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000, 'recipient': 'mẹ'},
            'expected_intent': 'SEND_MONEY',
            'expected_updated_params': {'amount': 2000000, 'recipient': 'chị'},
            'expected_preserved_params': {},
        },
        # Vietnamese - User sửa bill amount
        {
            'text': 'Không, 300 nghìn',
            'hint_intent_type': 'CREATE_BILL',
            'form_data': {'bill_name': 'Tiền điện', 'amount': 200000, 'due_date': '2024-12-15'},
            'expected_intent': 'CREATE_BILL',
            'expected_updated_params': {'amount': 300000},
            'expected_preserved_params': {'bill_name': 'Tiền điện', 'due_date': '2024-12-15'},
        },
        # English - User updates amount
        {
            'text': 'No, make it 1 million',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000, 'recipient': 'mom'},
            'expected_intent': 'SEND_MONEY',
            'expected_updated_params': {'amount': 1000000},
            'expected_preserved_params': {'recipient': 'mom'},
        },
        # English - User updates recipient
        {
            'text': 'Actually, send it to dad',
            'hint_intent_type': 'SEND_MONEY',
            'form_data': {'amount': 500000, 'recipient': 'mom'},
            'expected_intent': 'SEND_MONEY',
            'expected_updated_params': {'recipient': 'dad'},
            'expected_preserved_params': {'amount': 500000},
        },
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        hint_intent = test_case['hint_intent_type']
        form_data = test_case['form_data']
        expected_intent = test_case['expected_intent']
        expected_updated_params = test_case['expected_updated_params']
        expected_preserved_params = test_case['expected_preserved_params']

        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"📝 Input: '{text}'")
        print(f"🎯 Hint Intent: {hint_intent}")
        print(f"📋 Form Data (old): {form_data}")
        print(f"🎯 Expected Intent: {expected_intent}")
        print(f"🔄 Expected Updated Params: {expected_updated_params}")
        print(f"✅ Expected Preserved Params: {expected_preserved_params}")

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
            updated_correct = all(parameters.get(k) == v for k, v in expected_updated_params.items())
            preserved_correct = all(parameters.get(k) == v for k, v in expected_preserved_params.items())

            print(f"✅ Intent: {actual_intent}")
            print(f"📊 Confidence: {confidence:.2%}")
            print(f"📦 All Parameters: {parameters}")
            print(f"✅ Intent correct: {is_intent_correct}")
            print(f"✅ Updated params correct: {updated_correct}")
            print(f"✅ Preserved params correct: {preserved_correct}")

            if is_intent_correct and updated_correct and preserved_correct:
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
    asyncio.run(test_update_existing_params())
