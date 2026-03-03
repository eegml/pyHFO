# Fix: Meta parameter warnings when loading pretrained classification models

## Context

When loading HFO classification models via HuggingFace's `from_pretrained()`, dozens of warnings like this are emitted:

```
UserWarning: for conv1.weight: copying from a non-meta parameter in the checkpoint
to a meta parameter in the current model, which is a no-op.
```

**Root cause**: In `modeling_neuralcnn.py`, both `NeuralCNNModel` and `NeuralCNNForImageClassification` call `models.resnet18(weights=ResNet18_Weights.DEFAULT)` in `__init__`. Modern transformers (4.57+) wraps model creation in an `init_empty_weights()` context (meta device) during `from_pretrained()`. When torchvision's `resnet18()` internally calls `load_state_dict()` to load ImageNet weights into the meta-device model, it produces ~60 warnings per model. The ImageNet weights are then thrown away when transformers loads the actual HFO checkpoint weights.

The final model weights ARE correct (transformers has a fallback path), but the
warnings are noisy and confusing.

I suspect that this is because this is being loaded with in a context
loader which then causes another recursively. I think that you need to stop this
form happening in generally when loading models. [CLM]

## Fix

**File**: `pyhfo2app/dl_models/modeling_neuralcnn.py`

Change both model classes (lines 31 and 84) from:
```python
self.cnn = models.resnet18(weights=ResNet18_Weights.DEFAULT)
```
to:
```python
self.cnn = models.resnet18(weights=None)
```

Also remove the now-unused `ResNet18_Weights` import from line 9.

This is safe because:
- The ImageNet weights are always overwritten by HFO-specific weights from the checkpoint
- Verified that the fix produces identical model weights (tested `fc_out`, `layer4.1.conv2`, etc.)
- Verified zero meta-parameter warnings after the fix

## Verification

```bash
pyhfoenv39/bin/python -W error -c "
import warnings
warnings.filterwarnings('error', message='.*meta parameter.*')
from pyhfo2app.dl_models import NeuralCNNForImageClassification
model = NeuralCNNForImageClassification.from_pretrained('roychowdhuryresearch/HFO-artifact')
print('No warnings - fc_out:', model.fc_out.weight.data.flatten()[:3])
"
```
