import flwr as fl
from typing import List, Tuple
from flwr.common import Metrics

def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Calculate the total number of examples processed by all connected clients
    total_examples = sum([num_examples for num_examples, _ in metrics])
    
    # Aggregate loss
    weighted_loss = sum([num_examples * m["loss"] for num_examples, m in metrics]) / total_examples
    
    print(f"\n========================================")
    print(f"📈 --- GLOBAL METRICS (Round Aggregation) ---")
    
    # Aggregate accuracy
    if all("accuracy" in m for _, m in metrics):
        weighted_acc = sum([num_examples * m["accuracy"] for num_examples, m in metrics]) / total_examples
        print(f"Global Accuracy: {weighted_acc:.4f} | Global Loss: {weighted_loss:.4f}")
        print(f"========================================\n")
        return {"accuracy": weighted_acc, "loss": weighted_loss}
    else:
        print(f"Global Loss: {weighted_loss:.4f} (Accuracy not provided by all clients)")
        print(f"========================================\n")
        return {"loss": weighted_loss}

def main():
    print("========================================")
    print("🏢 DevCorp HQ - Federated Server Starting")
    print("========================================")

    strategy = fl.server.strategy.FedAvg(
        fraction_fit=1.0,           
        fraction_evaluate=0.0,      
        min_fit_clients=2,          
        min_available_clients=2,    
        fit_metrics_aggregation_fn=weighted_average 
    )

    print("Waiting for Équipe Banque and Équipe Santé to connect on port 8080...")
    
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=3, round_timeout=3600.0), 
        strategy=strategy,
    )

if __name__ == "__main__":
    main()