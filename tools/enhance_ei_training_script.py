"""
Drishti Smart Stick - Enhance Edge Impulse Training Script
Applies:
1. Dropout(0.15) before detection head to curb overfitting.
2. ReduceLROnPlateau callback to dynamically lower LR when validation loss plateaus.
3. minimumConfidenceRating = 0.35 to compute val_f1 at the optimal threshold.
4. Extended spatial and color space augmentations.
"""

import requests

API_KEY = "ei_f6f7e400ef663cbdb2f53e05906703d28ce75fe82b6ded4d"
PROJECT_ID = 1146751
HEADERS = {"x-api-key": API_KEY}
BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"

with open("current_ei_script.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add Dropout before head
old_cut = "cut_point = mobile_net_v2.get_layer('block_6_expand_relu')\n    #! Now attach a small additional head on the MobileNet\n    model = Conv2D(filters=32, kernel_size=1, strides=1,\n                activation='relu', name='head')(cut_point.output)"
new_cut = "cut_point = mobile_net_v2.get_layer('block_6_expand_relu')\n    drop = tf.keras.layers.Dropout(0.15, name='head_dropout')(cut_point.output)\n    #! Now attach a small additional head on the MobileNet\n    model = Conv2D(filters=32, kernel_size=1, strides=1,\n                activation='relu', name='head')(drop)"

if old_cut in code:
    code = code.replace(old_cut, new_cut)
    print("[+] Added Dropout(0.15) to detection head.")
else:
    print("[-] Old cut point not matched exactly.")

# 2. Add ReduceLROnPlateau
old_cb = "callbacks.append(metrics.PrintPercentageTrained(num_epochs))"
new_cb = "callbacks.append(metrics.PrintPercentageTrained(num_epochs))\n    callbacks.append(tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=6, min_lr=1e-5, verbose=0))"

if old_cb in code:
    code = code.replace(old_cb, new_cb)
    print("[+] Added ReduceLROnPlateau callback.")
else:
    print("[-] Old callback point not matched exactly.")

# Upload enhanced script & parameters
payload = {
    "script": code,
    "minimumConfidenceRating": 0.35,
    "augmentationPolicyImage": "extended"
}

r = requests.post(f"{BASE_URL}/training/keras/3", headers=HEADERS, json=payload)
print("[+] Edge Impulse update status:", r.status_code, r.text)
