import numpy as np

filepath = r'C:\Users\ELITEBOOK X2\Desktop\HND EOT\PROJECT\polimi-ispl landmine_detection_autoencoder master datasets-giuriati_2\20170621_deg0_HHVV.npy'

try:
    data = np.load(filepath, allow_pickle=True)
    if data.ndim == 0:
        content = data.item()
        gt = content.get('ground_truth')
        print("Ground Truth values:", gt)
        print("Unique values:", np.unique(gt))
except Exception as e:
    print("Error:", e)
