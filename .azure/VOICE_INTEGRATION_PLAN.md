# Voice Form Integration - Implementation Status

## ✅ COMPLETED - Zustand Migration

### 1. State Management với Zustand

**Files created:**

- ✅ `lib/stores/app-store.ts` - App global state
  - currentPage, currentDialog
  - isProcessingVoice, isRecording
  - voiceLoadingMode
- ✅ `lib/stores/form-store.ts` - Form data state
  - type, data, isDialogOpen
  - updateFormData, clearForm

**Benefits:**

- 🚀 Devtools enabled (debug dễ dàng)
- ⚡ Selective subscriptions (ít re-render)
- 🎯 Không cần Provider nesting
- 📦 Bundle size nhỏ hơn

### 2. Updated Components

**Files updated:**

- ✅ `lib/speech-context.tsx`
  - Dùng useAppStore, useFormStore
  - startListening gửi full context (formData, currentPage, currentDialog)
  - Sync isRecording, isProcessingVoice với store
- ✅ `components/layout/navbar.tsx`
  - Dùng stores thay vì Context
  - Desktop mic button z-60 (always visible)
- ✅ `components/speech/speech-button.tsx`
  - Dùng FormStore để get form data
- ✅ `app/layout.tsx`
  - Removed FormProvider, AppStateProvider
  - Cleaner provider tree

### 3. Voice Processing UI

- ✅ `VoiceProcessingOverlay` component integrated
- ✅ Sync processing state between Speech và AppStore

---

## 🚧 IN PROGRESS - Dialog Integration

### 4. Dialog Components cần update

**Pattern chung cho tất cả dialog forms:**

```typescript
import { useAppStore } from "@/lib/stores/app-store";
import { useFormStore } from "@/lib/stores/form-store";

export function TransferForm() {
  // Get states
  const isRecording = useAppStore((state) => state.isRecording);
  const openDialog = useAppStore((state) => state.openDialog);
  const closeDialog = useAppStore((state) => state.closeDialog);
  const setCurrentForm = useFormStore((state) => state.setCurrentForm);
  const updateFormData = useFormStore((state) => state.updateFormData);

  // Sync dialog state
  const [open, setOpen] = useState(false);

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && isRecording) {
      // Prevent close khi đang recording
      return;
    }

    setOpen(newOpen);
    if (newOpen) {
      openDialog("transfer", formData);
      setCurrentForm("create_transfer", formData, true);
    } else {
      closeDialog();
      setCurrentForm(null, {}, false);
    }
  };

  // Update form khi input change
  const handleFieldChange = (field: string, value: any) => {
    updateFormData({ [field]: value });
  };
}
```

**Files cần update:**

- [ ] `components/financial/transfer-form.tsx`
- [ ] `components/financial/bill-form.tsx`
- [ ] `components/financial/fund-form.tsx`
- [ ] `components/financial/deposit-withdraw-form.tsx`

---

## 📋 TODO - Backend Integration

### 5. Backend Context-Aware Intent Detection

**Init message structure** (Frontend đã gửi):

```json
{
  "type": "init",
  "intent_type": "create_transfer",  // from FormStore
  "form_data": {
    "amount": 1000000,
    "recipient": "..."
  },
  "current_page": "/accounts",       // from pathname
  "current_dialog": {                // from AppStore
    "type": "transfer",
    "data": {...}
  }
}
```

**Backend Intent Service Prompt Engineering:**

```python
# api/src/application/services/intent_service.py

CONTEXT_AWARE_PROMPT = """
Bạn là trợ lý tài chính thông minh. Phân tích lệnh giọng nói với context sau:

**Current Context:**
- Page: {current_page}
- Dialog: {current_dialog_type} (đang mở: {is_dialog_open})
- Form data hiện tại: {form_data}

**Rules:**
1. Nếu user KHÔNG NÓI RÕ intent (vd: chỉ nói "500 nghìn"):
   - Kiểm tra `current_dialog.type` → đó là intent
   - Xác định field nào đang thiếu trong `form_data`
   - Return action: "update_form" với field đó

2. Nếu user NÓI RÕ intent (vd: "chuyển tiền 500k"):
   - Parse intent mới
   - So sánh với current_dialog
   - Nếu khác → action: "navigate" hoặc "open_dialog"
   - Nếu giống → action: "update_form"

3. Nếu đang ở dashboard (không có dialog):
   - Phải có intent rõ ràng
   - action: "navigate" + "open_dialog"

**Output format:**
{
  "action": "navigate" | "open_dialog" | "update_form" | "stay",
  "intent_type": "create_transfer",
  "parameters": {...},
  "navigation": {
    "page": "/accounts",
    "dialog": "transfer"
  }
}
"""
```

**Intent Service Enhancement:**

```python
class IntentService:
    def classify_with_context(
        self,
        asr_text: str,
        current_page: str,
        current_dialog: dict,
        form_data: dict
    ) -> dict:
        # 1. Extract raw intent
        raw_intent = self.llm.extract_intent(asr_text)

        # 2. Context-aware classification
        if not raw_intent.is_explicit:
            # User chỉ nói value, không nói intent
            if current_dialog and current_dialog.get("type"):
                return {
                    "action": "update_form",
                    "intent_type": current_dialog["type"],
                    "parameters": self._map_values_to_fields(
                        raw_intent.values,
                        form_data
                    )
                }

        # 3. Intent changed?
        if current_dialog and raw_intent.type != current_dialog.get("type"):
            return {
                "action": "open_dialog",  # hoặc "navigate"
                "intent_type": raw_intent.type,
                "parameters": raw_intent.parameters
            }

        # 4. Same intent, update data
        return {
            "action": "update_form",
            "intent_type": raw_intent.type,
            "parameters": raw_intent.parameters
        }
```

---

### 6. Frontend Response Handler

**Update `speech-context.tsx` - onIntentExtracted:**

```typescript
onIntentExtracted: (data) => {
  const { action, intent_type, parameters, navigation } = data;

  switch (action) {
    case "navigate":
      router.push(navigation.page);
      if (navigation.dialog) {
        setTimeout(() => {
          useAppStore.getState().openDialog(navigation.dialog, parameters);
          useFormStore.getState().setCurrentForm(intent_type, parameters, true);
        }, 300);
      }
      toast.success("Đã chuyển trang");
      break;

    case "open_dialog":
      useAppStore.getState().openDialog(navigation.dialog, parameters);
      useFormStore.getState().setCurrentForm(intent_type, parameters, true);
      toast.success("Đã mở form");
      break;

    case "update_form":
      useFormStore.getState().updateFormData(parameters);
      toast.success("Đã cập nhật form");
      break;

    case "stay":
      // Do nothing, just show confirmation
      toast.info("Vui lòng bổ sung thêm thông tin");
      break;
  }

  disconnect();
};
```

---

## 🧪 Testing Scenarios

### Scenario 1: Edit field trong dialog

1. Mở transfer dialog
2. Nhập recipient: "Nam"
3. Click mic → nói "500 nghìn"
4. ✅ Expected: Form amount = 500000, dialog không đóng

### Scenario 2: Change intent

1. Đang ở transfer dialog
2. Click mic → nói "tạo hóa đơn điện 200k"
3. ✅ Expected: Navigate to /bills, open bill dialog

### Scenario 3: New intent from dashboard

1. Ở dashboard (không có dialog)
2. Click mic → nói "chuyển 1 triệu cho Huy"
3. ✅ Expected: Navigate to /accounts, open transfer dialog, fill data

### Scenario 4: Recording không đóng dialog

1. Mở bất kỳ dialog nào
2. Click mic (đang recording)
3. Click outside dialog
4. ✅ Expected: Dialog KHÔNG đóng

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────┐
│           Zustand Stores                    │
├─────────────────────────────────────────────┤
│  AppStore                FormStore          │
│  - currentPage           - type             │
│  - currentDialog         - data             │
│  - isRecording          - isDialogOpen      │
│  - isProcessingVoice                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Speech Context (Manager)            │
│  - startListening(formData, intentType)     │
│  - Send: formData + currentPage + dialog    │
│  - Receive: action + intent + parameters    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│              Backend                        │
│  Intent Service (Context-Aware)             │
│  - Parse with context                       │
│  - Return: action type                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Response Handler                    │
│  - navigate → router.push + openDialog      │
│  - open_dialog → openDialog + setForm       │
│  - update_form → updateFormData             │
└─────────────────────────────────────────────┘
```

---

## 🎯 Next Steps

1. **Update Dialog Components** (1-2 giờ)

   - Implement pattern trên cho 4 form components
   - Test prevent close khi recording

2. **Backend Prompt Engineering** (1 giờ)

   - Update intent service với context awareness
   - Define response action types
   - Test với các scenarios

3. **Frontend Response Handler** (30 phút)

   - Implement switch case cho actions
   - Test navigation + dialog opening

4. **E2E Testing** (1 giờ)
   - Test 4 scenarios trên
   - Fix bugs nếu có

**Total estimate: 3.5 - 4.5 giờ**

### 1. Global State Management

- ✅ Tạo `app-state-context.tsx` để quản lý:

  - `currentPage`: Track trang hiện tại
  - `currentDialog`: Track dialog đang mở (type, isOpen, data)
  - `isProcessingVoice`: State xử lý voice
  - `voiceLoadingMode`: "loading" hoặc "ignore"

- ✅ Cập nhật `form-context.tsx`:

  - Thêm `isDialogOpen` flag
  - Thêm `updateFormData` method

- ✅ Thêm providers vào `layout.tsx`

### 2. Voice Recording Flow Enhancement

- ✅ Cập nhật `speech-context.tsx`:
  - Import `usePathname` và `useAppState`
  - Gửi `currentPage`, `currentDialog` kèm theo form data
  - Tạo `updateProcessingState` để sync với AppState

### 3. UI Components

- ✅ Tạo `VoiceProcessingOverlay` component
  - Hiển thị loading khi `isProcessingVoice = true`
  - Animation progress bar
  - Prevent scroll khi active

## 🚧 Đang làm

### 4. Sync Processing State

**File**: `app/lib/speech-context.tsx`

**Cần làm**: Replace tất cả `setIsProcessing` calls với `updateProcessingState`

Vị trí cần thay (12 chỗ):

- Line 135, 250, 271, 285, 516, 552: `setIsProcessing(false)`
- Line 420, 529: `setIsProcessing(true)`

## 📋 Chưa làm

### 5. Dialog & Navbar Behavior

#### a. Dialog Components

**Files cần sửa**:

- `components/financial/transfer-form.tsx`
- `components/financial/bill-form.tsx`
- `components/financial/fund-form.tsx`
- `components/financial/deposit-withdraw-form.tsx`

**Yêu cầu**:

- Thêm prop `preventClose` vào Dialog
- Khi `isListening = true`, dialog không đóng khi click outside
- Sync dialog state với `AppState.currentDialog`

#### b. Navbar Mobile

**File**: `components/layout/navbar.tsx`

**Yêu cầu**:

- Mobile: Navbar KHÔNG blur khi dialog mở
- Desktop: Mic button luôn visible
- Cả 2: Recording dialog vẫn show trên dialog form

### 6. Backend Enhancement

**File backend cần update**: `api/src/application/use_cases/...`

**Init message structure** (đã gửi từ frontend):

```json
{
  "type": "init",
  "intent_type": "create_transfer",
  "form_data": {
    "amount": 1000000,
    "recipient": "..."
  },
  "current_page": "/accounts",
  "current_dialog": {
    "type": "transfer",
    "data": {...}
  }
}
```

**Intent Service cần xử lý**:

1. Nếu user không nói rõ intent → check `current_dialog.type` hoặc `current_page`
2. Nếu chỉ nói field value → edit field trong `form_data`
3. Return response với action type

### 7. Backend Response Handler

**Response structure cần định nghĩa**:

```json
{
  "type": "intent_extracted",
  "action": "navigate" | "open_dialog" | "update_form" | "stay",
  "intent_type": "create_transfer",
  "parameters": {...},
  "navigation": {
    "page": "/accounts",
    "dialog": "transfer"
  }
}
```

**Frontend xử lý**:

- `navigate`: Router push + open dialog if needed
- `open_dialog`: AppState.openDialog()
- `update_form`: FormContext.updateFormData()
- `stay`: Giữ nguyên, chỉ update form data

### 8. Voice Processing Loading Mode

**Cần thêm vào SpeechContext**:

```typescript
// Option 1: Loading overlay (block UI)
setVoiceLoadingMode("loading");

// Option 2: Ignore (không block UI)
setVoiceLoadingMode("ignore");
```

User có thể config trong settings.

## 🔧 Integration Steps

### Step 1: Hoàn thành Sync State (đang làm)

```bash
# Tìm và thay trong speech-context.tsx
setIsProcessing(true) → updateProcessingState(true)
setIsProcessing(false) → updateProcessingState(false)
```

### Step 2: Thêm VoiceProcessingOverlay vào layout

```tsx
// app/app/layout.tsx
import { VoiceProcessingOverlay } from "@/components/speech/voice-processing-overlay";

// Trong return
<SpeechProvider>
  {children}
  <VoiceProcessingOverlay />
</SpeechProvider>;
```

### Step 3: Update Dialog Components

Mỗi form component (transfer, bill, fund, etc):

1. Import `useAppState` và `useSpeech`
2. Sync dialog open/close với AppState
3. Update form data to FormContext khi user nhập
4. Prevent close khi `isListening = true`

### Step 4: Update Backend

1. Modify init message handler để nhận context
2. Enhance intent classifier với context awareness
3. Return structured response với action type

### Step 5: Handle Response Actions

Update `onIntentExtracted` trong speech-context để:

- Parse action type
- Execute appropriate action
- Show toast notification

## 📝 Notes

- **Dialog State Tracking**: Mỗi khi mở dialog → `AppState.openDialog(type, data)`
- **Form Data Tracking**: Mỗi khi thay đổi form → `FormContext.updateFormData(data)`
- **Page Tracking**: Router change → `AppState.setCurrentPage(page)`
- **Voice Loading**: Có thể là overlay hoặc ignore, tùy user preference

## 🧪 Testing Checklist

- [ ] Open transfer dialog → say amount → form auto-fill
- [ ] In transfer dialog → say "chuyển 500k cho Nam" → stay in dialog, update data
- [ ] In dashboard → say "tạo hóa đơn điện 200k" → navigate + open bill dialog
- [ ] Dialog không đóng khi recording
- [ ] Navbar visible trên mobile khi dialog mở
- [ ] Mic button visible trên desktop
- [ ] Voice processing overlay shows/hides correctly
- [ ] Form data persist across voice interactions
