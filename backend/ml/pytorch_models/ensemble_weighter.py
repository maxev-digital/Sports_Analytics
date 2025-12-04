"""
Neural Ensemble Weighter
Learns optimal weights for combining 7 models dynamically
"""
import torch
import torch.nn as nn
import numpy as np

class EnsembleWeighter(nn.Module):
    def __init__(self, n_models=7):
        super().__init__()
        # Input: predictions from N models + recent accuracy of each
        # Output: weighted combination
        self.network = nn.Sequential(
            nn.Linear(n_models * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, n_models),
            nn.Softmax(dim=1)  # Weights must sum to 1
        )

    def forward(self, model_predictions, model_accuracies):
        """
        model_predictions: (batch, n_models) - predictions from each model
        model_accuracies: (batch, n_models) - recent accuracy of each model
        """
        x = torch.cat([model_predictions, model_accuracies], dim=1)
        weights = self.network(x)
        # Weighted sum of predictions
        weighted_pred = (model_predictions * weights).sum(dim=1)
        return weighted_pred, weights

class EnsembleWeighterTrainer:
    def __init__(self, n_models=7, lr=0.001, device='cpu'):
        self.device = torch.device(device)
        self.model = EnsembleWeighter(n_models=n_models).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        self.n_models = n_models

    def train(self, all_model_preds, model_accuracies, y_true, epochs=50, batch_size=32):
        """
        all_model_preds: (n_samples, n_models) - predictions from all models
        model_accuracies: (n_samples, n_models) - accuracy history for each model
        y_true: (n_samples,) - actual outcomes
        """
        X_preds = torch.FloatTensor(all_model_preds).to(self.device)
        X_accs = torch.FloatTensor(model_accuracies).to(self.device)
        y = torch.FloatTensor(y_true).to(self.device)

        for epoch in range(epochs):
            self.model.train()

            indices = torch.randperm(len(X_preds))
            for i in range(0, len(X_preds), batch_size):
                batch_indices = indices[i:i+batch_size]
                batch_preds = X_preds[batch_indices]
                batch_accs = X_accs[batch_indices]
                batch_y = y[batch_indices]

                self.optimizer.zero_grad()
                outputs, weights = self.model(batch_preds, batch_accs)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()

            if (epoch + 1) % 10 == 0:
                print(f"Ensemble Weighter Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

        return self.model

    def predict(self, all_model_preds, model_accuracies):
        """Generate weighted ensemble predictions"""
        self.model.eval()
        with torch.no_grad():
            X_preds = torch.FloatTensor(all_model_preds).to(self.device)
            X_accs = torch.FloatTensor(model_accuracies).to(self.device)
            predictions, weights = self.model(X_preds, X_accs)

        return predictions.cpu().numpy(), weights.cpu().numpy()

    def save(self, path):
        """Save model"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'n_models': self.n_models
        }, path)

    def load(self, path):
        """Load model"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        return self.model
