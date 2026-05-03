"""
V42 神經意圖分類器整合代碼
訓練日期: 2026-04-08
驗證準確率: 0.8907
意圖類別: 28 類

整合方式：將此代碼插入 christine_final.py 的 V42GigaSpeaker 類別中，
替換現有的 _ml_classify() 方法
"""

_V42_NEURAL_MODEL = None
_V42_NEURAL_LOADED = False
_V42_NEURAL_PATH = r"f:\\v42_export\\v42_neural_intent"

def _load_neural_model():
    global _V42_NEURAL_MODEL, _V42_NEURAL_LOADED
    if _V42_NEURAL_LOADED:
        return _V42_NEURAL_MODEL
    _V42_NEURAL_LOADED = True
    try:
        import torch
        import torch.nn as nn
        import sys
        # 加入 F 槽 torch 路徑
        if "F:\\py_site310" not in sys.path:
            sys.path.insert(0, "F:\\py_site310")
        from sentence_transformers import SentenceTransformer
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        enc_path = os.path.join(_V42_NEURAL_PATH, "encoder")
        clf_path = os.path.join(_V42_NEURAL_PATH, "classifier.pt")
        
        if not os.path.exists(enc_path) or not os.path.exists(clf_path):
            return None
        
        encoder = SentenceTransformer(enc_path).to(device)
        clf_data = torch.load(clf_path, map_location=device)
        
        hidden_size = clf_data["hidden_size"]
        classifier = nn.Sequential(
            nn.Linear(hidden_size, 512), nn.GELU(), nn.Dropout(0.1),
            nn.Linear(512, 256), nn.GELU(), nn.Dropout(0.1),
            nn.Linear(256, len(clf_data["label2id"]))
        ).to(device)
        classifier.load_state_dict(clf_data["classifier"])
        classifier.eval()
        encoder.eval()
        
        _V42_NEURAL_MODEL = {
            "encoder": encoder,
            "classifier": classifier,
            "id2label": clf_data["id2label"],
            "label2id": clf_data["label2id"],
            "device": device,
            "val_accuracy": clf_data.get("val_accuracy", 0),
        }
        acc = clf_data.get("val_accuracy", 0)
        print(f"[V42-Neural] ✅ 神經意圖模型已載入 (acc={acc:.4f}, device={device})")
        return _V42_NEURAL_MODEL
    except Exception as e:
        print(f"[V42-Neural] ⚠️  模型載入失敗: {e}")
        return None

def _neural_classify(self, il):
    """Level 0.6 升級版：神經網路意圖分類（取代 TF-IDF+LinearSVC）
    
    優勢：
    - 不受固定詞彙表限制（sentence-transformer 使用子詞分詞）
    - 支援語意理解（"好開心" 和 "非常快樂" 會被視為相似）
    - 中英文混合輸入自然支援
    - 可持續學習（fine-tuning）
    """
    try:
        import torch
        import torch.nn.functional as F
        
        model = _load_neural_model()
        if model is None:
            return None
        
        encoder = model["encoder"]
        classifier = model["classifier"]
        id2label = model["id2label"]
        device = model["device"]
        
        with torch.no_grad():
            emb = encoder.encode([il], convert_to_tensor=True,
                                  show_progress_bar=False, device=device)
            logits = classifier(emb)
            probs = F.softmax(logits, dim=-1)[0]
            
            top2 = torch.topk(probs, 2)
            top_prob = top2.values[0].item()
            second_prob = top2.values[1].item()
            top_id = top2.indices[0].item()
            
            pred_label = id2label[top_id]
            # 信心 = top1 機率 × (1 + gap_ratio)
            gap = top_prob - second_prob
            confidence = min(0.97, top_prob * (1 + gap))
        
        if confidence < 0.55:
            return None
        
        return pred_label, round(confidence, 3)
        
    except Exception:
        return None
