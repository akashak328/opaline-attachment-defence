"""
model_training.py
─────────────────
CANet model: trains a DistilBERT-based binary classifier
to distinguish malicious (spam) from safe (ham) email attachments.

Architecture:
  DistilBERT (frozen/fine-tuned) → Dropout → Linear → Sigmoid (binary output)
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertModel, DistilBertTokenizer
from tqdm import tqdm
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

# ── Hyperparameters ────────────────────────────────────────────────────────────
MAX_LEN          = 512
TRAIN_BATCH_SIZE = 8
VALID_BATCH_SIZE = 4
EPOCHS           = 3
LEARNING_RATE    = 1e-5
MODEL_NAME       = "distilbert-base-uncased"
MODEL_SAVE_PATH  = "static/canet_model.pt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[INFO] Using device: {device}")


# ── Dataset Class ──────────────────────────────────────────────────────────────

class SentimentData(Dataset):
    """
    Tokenizes email text and returns tensors for DistilBERT input.
    Labels: 0 = ham (safe), 1 = spam (malicious)
    """

    def __init__(self, dataframe: pd.DataFrame, tokenizer, max_len: int):
        self.data      = dataframe.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_len   = max_len
        # Encode labels: spam → 1, ham → 0
        self.targets   = self.data['Classify'].apply(lambda x: 1 if x == 'spam' else 0).values
        self.text      = self.data['Email'].values

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        text = str(self.text[index])
        text = " ".join(text.split())

        inputs = self.tokenizer.encode_plus(
            text,
            None,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_token_type_ids=True
        )

        return {
            'ids':             torch.tensor(inputs['input_ids'],      dtype=torch.long),
            'mask':            torch.tensor(inputs['attention_mask'],  dtype=torch.long),
            'token_type_ids':  torch.tensor(inputs['token_type_ids'], dtype=torch.long),
            'targets':         torch.tensor(self.targets[index],       dtype=torch.long)
        }


# ── CANet Model ────────────────────────────────────────────────────────────────

class CANetModel(nn.Module):
    """
    Content-Aware Network (CANet):
    DistilBERT encoder + classification head.
    """

    def __init__(self, num_classes: int = 2):
        super(CANetModel, self).__init__()
        self.distilbert  = DistilBertModel.from_pretrained(MODEL_NAME)
        self.dropout     = nn.Dropout(0.3)
        self.classifier  = nn.Linear(768, num_classes)

    def forward(self, ids, mask, token_type_ids=None):
        output      = self.distilbert(input_ids=ids, attention_mask=mask)
        hidden_state = output.last_hidden_state        # (batch, seq_len, 768)
        pooled       = hidden_state[:, 0]              # [CLS] token
        pooled       = self.dropout(pooled)
        logits       = self.classifier(pooled)
        return logits


# ── Accuracy Helper ────────────────────────────────────────────────────────────

def calculate_accuracy(preds, targets):
    _, predicted = torch.max(preds, dim=1)
    correct      = (predicted == targets).sum().item()
    return correct


# ── Training Loop ──────────────────────────────────────────────────────────────

def train(epoch: int, model, loader, optimizer, loss_fn):
    model.train()
    tr_loss, n_correct, nb_steps, nb_examples = 0, 0, 0, 0

    for step, data in tqdm(enumerate(loader), total=len(loader), desc=f"Epoch {epoch}"):
        ids             = data['ids'].to(device, dtype=torch.long)
        mask            = data['mask'].to(device, dtype=torch.long)
        token_type_ids  = data['token_type_ids'].to(device, dtype=torch.long)
        targets         = data['targets'].to(device, dtype=torch.long)

        outputs = model(ids, mask, token_type_ids)
        loss    = loss_fn(outputs, targets)

        tr_loss    += loss.item()
        n_correct  += calculate_accuracy(outputs, targets)
        nb_steps   += 1
        nb_examples += targets.size(0)

        if step % 500 == 0 and step > 0:
            print(f"  Step {step} | Loss: {tr_loss/nb_steps:.4f} | Acc: {n_correct*100/nb_examples:.2f}%")

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    epoch_loss = tr_loss / nb_steps
    epoch_acc  = n_correct * 100 / nb_examples
    print(f"[Train] Epoch {epoch} → Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.2f}%")
    return epoch_acc


# ── Validation Loop ────────────────────────────────────────────────────────────

def valid(model, loader, loss_fn):
    model.eval()
    tr_loss, n_correct, nb_steps, nb_examples = 0, 0, 0, 0

    with torch.no_grad():
        for step, data in tqdm(enumerate(loader), total=len(loader), desc="Validating"):
            ids             = data['ids'].to(device, dtype=torch.long)
            mask            = data['mask'].to(device, dtype=torch.long)
            token_type_ids  = data['token_type_ids'].to(device, dtype=torch.long)
            targets         = data['targets'].to(device, dtype=torch.long)

            outputs = model(ids, mask, token_type_ids)
            loss    = loss_fn(outputs, targets)

            tr_loss    += loss.item()
            n_correct  += calculate_accuracy(outputs, targets)
            nb_steps   += 1
            nb_examples += targets.size(0)

    epoch_loss = tr_loss / nb_steps
    epoch_acc  = n_correct * 100 / nb_examples
    print(f"[Valid] Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.2f}%")
    return epoch_acc


# ── Full Training Pipeline ─────────────────────────────────────────────────────

def run_training(csv_path: str = "static/dataset/spam.csv"):
    print("[INFO] Loading tokenizer and dataset...")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

    df = pd.read_csv(csv_path, encoding="ISO-8859-1")
    df = df.rename(columns={"v1": "Classify", "v2": "Email"})
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["Email"], inplace=True)

    train_size = 0.8
    train_df   = df.sample(frac=train_size, random_state=200)
    test_df    = df.drop(train_df.index).reset_index(drop=True)
    train_df   = train_df.reset_index(drop=True)

    print(f"[INFO] Full: {df.shape} | Train: {train_df.shape} | Test: {test_df.shape}")

    training_set = SentimentData(train_df, tokenizer, MAX_LEN)
    testing_set  = SentimentData(test_df,  tokenizer, MAX_LEN)

    train_loader = DataLoader(training_set, batch_size=TRAIN_BATCH_SIZE, shuffle=True,  num_workers=0)
    test_loader  = DataLoader(testing_set,  batch_size=VALID_BATCH_SIZE, shuffle=False, num_workers=0)

    model     = CANetModel(num_classes=2).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn   = nn.CrossEntropyLoss()

    best_acc = 0
    for epoch in range(1, EPOCHS + 1):
        train_acc = train(epoch, model, train_loader, optimizer, loss_fn)
        val_acc   = valid(model, test_loader, loss_fn)
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"[INFO] Best model saved (val_acc={val_acc:.2f}%) → {MODEL_SAVE_PATH}")

    print(f"[DONE] Training complete. Best validation accuracy: {best_acc:.2f}%")
    return model


if __name__ == "__main__":
    run_training()
