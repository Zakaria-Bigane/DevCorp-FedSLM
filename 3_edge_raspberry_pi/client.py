import flwr as fl
import torch
import json
import multiprocessing
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from collections import OrderedDict

# ===== OPTIMIZED HARDWARE CONFIG =====
# Use the uncompressed model directory for native CPU speed
MODEL_PATH = "./devcorp-unified-0.5b" 
DATA_FILE = "banque_data.jsonl"       # Change to sante_data.jsonl for the other Pi
MAX_LENGTH = 48                    
LORA_R = 4
LR = 1e-4

# Unleash the full quad-core processor
torch.set_num_threads(multiprocessing.cpu_count())
# =====================================

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading model natively into CPU RAM...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, 
    device_map="cpu", 
    torch_dtype=torch.float32, 
    low_cpu_mem_usage=True
)
model = get_peft_model(model, LoraConfig(r=LORA_R, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))

print("Loading and tokenizing data...")
with open(DATA_FILE, "r") as f:
    data = [json.loads(line) for line in f]

input_ids_list = []
for item in data:
    tokens = tokenizer(item["text"], truncation=True, max_length=MAX_LENGTH, return_tensors="pt", padding=False)
    input_ids_list.append(tokens["input_ids"][0])

class EdgeClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [val.cpu().detach().numpy() for _, val in model.named_parameters() if val.requires_grad]

    def set_parameters(self, parameters):
        keys = [k for k, v in model.named_parameters() if v.requires_grad]
        for k, p in zip(keys, parameters):
            model.get_parameter(k).data = torch.tensor(p)

    def fit(self, parameters, config):
        print("\n--- HQ TRIGGERED TRAINING ROUND ---")
        self.set_parameters(parameters)
        model.train()
        optimizer = torch.optim.AdamW(model.parameters(), lr=LR)

        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        for idx, ids in enumerate(input_ids_list):
            optimizer.zero_grad()
            ids = ids.unsqueeze(0).to(model.device)
            out = model(ids, labels=ids)
            
            loss = out.loss
            loss.backward()
            optimizer.step()
            
            # --- RESTORED CAUSAL ACCURACY MATH ---
            with torch.no_grad():
                shift_logits = out.logits[..., :-1, :].contiguous()
                shift_labels = ids[..., 1:].contiguous()
                predictions = torch.argmax(shift_logits, dim=-1)
                
                total_correct += (predictions == shift_labels).sum().item()
                total_samples += shift_labels.numel()
            
            total_loss += loss.item()
            print(f"Sample {idx+1}/{len(input_ids_list)} | Loss: {loss.item():.4f}")

        avg_loss = total_loss / len(input_ids_list)
        accuracy = total_correct / total_samples if total_samples > 0 else 0
        
        print(f"✅ Local Round Complete -> Avg Loss: {avg_loss:.4f} | Accuracy: {accuracy:.4f}")
        
        return self.get_parameters({}), len(input_ids_list), {"loss": float(avg_loss), "accuracy": float(accuracy)}

print("\nConnecting to DevCorp HQ...")
fl.client.start_client(server_address="192.168.0.102:8080", client=EdgeClient().to_client())