"""
Integration test for Intent Service with REAL Gemini API
Chạy: python api/test_intent_integration.py
"""
from __future__ import annotations

import asyncio
import sys

from application.services.intent_service import IntentUnderstandingInput
from application.services.intent_service import IntentUnderstandingService
from domain.plugins.registry import IntentPluginRegistry
from infra.llm.llm_service import LLMService
from shared.settings import Settings


async def test_real_intent_classification():
    """Test Intent Service với Gemini API thực"""

    print('\n' + '=' * 60)
    print('  INTENT SERVICE - INTEGRATION TEST WITH GEMINI')
    print('=' * 60 + '\n')

    # Setup
    settings = Settings()
    llm_service = LLMService(settings)
    plugin_registry = IntentPluginRegistry()

    # IMPORTANT: Discover plugins!
    plugin_registry.discover_plugins()

    # Initialize Intent Service
    intent_service = IntentUnderstandingService(
        settings=settings,
        llm_service=llm_service,
        plugin_registry=plugin_registry,
    )

    # Test cases
    test_cases = [
        {
            'text': 'Chuyển 500 nghìn cho mẹ',
            'expected_intent': 'SEND_MONEY',
        },
        {
            'text': 'Xem số dư tài khoản',
            'expected_intent': 'CHECK_BALANCE',
        },
        {
            'text': 'Tạo hóa đơn tiền điện 200 nghìn, hạn ngày 15',
            'expected_intent': 'CREATE_BILL',
        },
        {
            'text': 'Tạo quỹ tiết kiệm mua xe 50 triệu',
            'expected_intent': 'CREATE_FUND',
        },
        {
            'text': 'Hôm nay thời tiết thế nào',
            'expected_intent': 'UNKNOWN',
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        expected = test_case['expected_intent']

        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"📝 Input: '{text}'")
        print(f"🎯 Expected: {expected}")

        try:
            # Process intent
            input_data = IntentUnderstandingInput(text=text, context={})
            result = await intent_service.process(input_data)

            # Display results
            actual = result.intent_type.value
            confidence = result.confidence
            parameters = result.parameters

            is_correct = actual == expected
            status = '✅ PASS' if is_correct else '❌ FAIL'

            print(f"🤖 Actual: {actual}")
            print(f"📊 Confidence: {confidence:.2%}")
            print(f"📦 Parameters: {parameters}")
            print(f"   {status}")

            results.append({
                'text': text,
                'expected': expected,
                'actual': actual,
                'confidence': confidence,
                'parameters': parameters,
                'passed': is_correct,
            })

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                'text': text,
                'expected': expected,
                'actual': 'ERROR',
                'confidence': 0.0,
                'parameters': {},
                'passed': False,
            })

    # Summary
    print('\n' + '=' * 60)
    print('SUMMARY')
    print('=' * 60)

    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    accuracy = passed / total * 100 if total > 0 else 0

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Accuracy: {accuracy:.1f}%")

    print('\nDetailed Results:')
    print('-' * 60)
    for i, r in enumerate(results, 1):
        status = '✅' if r['passed'] else '❌'
        print(f"{i}. {status} '{r['text'][:40]}...'")
        print(f"   Expected: {r['expected']} | Actual: {r['actual']} | Conf: {r['confidence']:.0%}")

    if accuracy == 100:
        print('\n🎉 Perfect! All tests passed!')
    elif accuracy >= 80:
        print('\n👍 Good! Most tests passed.')
    else:
        print('\n⚠️ Needs improvement. Check Gemini responses.')


async def test_normalize_amount():
    """Test normalize amount function"""

    print('\n' + '=' * 60)
    print('  TEST NORMALIZE AMOUNT')
    print('=' * 60 + '\n')

    settings = Settings()
    llm_service = LLMService(settings)
    plugin_registry = IntentPluginRegistry()

    # Discover plugins
    plugin_registry.discover_plugins()

    intent_service = IntentUnderstandingService(
        settings=settings,
        llm_service=llm_service,
        plugin_registry=plugin_registry,
    )

    test_cases = [
        ('500 nghìn', 500000),
        ('1 triệu', 1000000),
        ('1.5 triệu', 1500000),
        ('2,5 nghìn', 2500),
        ('500000', 500000),
        (500000, 500000),
    ]

    passed = 0
    for input_val, expected in test_cases:
        actual = intent_service._normalize_amount(input_val)
        is_correct = actual == expected
        status = '✅' if is_correct else '❌'

        print(f"{status} '{input_val}' -> {actual:,.0f} (expected: {expected:,.0f})")
        if is_correct:
            passed += 1

    print(f"\nPassed: {passed}/{len(test_cases)}")


async def main():
    print('\n' + '🚀 ' + '=' * 58)
    print('   INTENT SERVICE INTEGRATION TEST')
    print('=' * 60 + '\n')

    try:
        # Test 1: Normalize amount (không cần API)
        await test_normalize_amount()

        # Test 2: Real intent classification (cần Gemini API)
        await test_real_intent_classification()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print('\n' + '=' * 60)
    print('  TEST COMPLETE')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    asyncio.run(main())
