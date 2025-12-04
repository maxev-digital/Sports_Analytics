"""
PyTorch Tabular Neural Network for Sports Betting
6-layer residual network optimized for 78-feature inputs
"""
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import joblib

class TabularNet(nn.Module):
    def __init__(self, input_dim=78, hidden_dims=[256, 512, 256, 128, 64], dropout=0.3):
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        # Output layer for regression (predicting totals/spreads)
        layers.append(nn.Linear(prev_dim, 1))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class TabularNetTrainer:
    def __init__(self, input_dim=78, lr=0.001, device='cpu'):
        self.device = torch.device(device)
        self.model = TabularNet(input_dim=input_dim).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()

    def train(self, X_train, y_train, epochs=100, batch_size=32, validation_split=0.2):
        """Train the model"""
        X = torch.FloatTensor(X_train).to(self.device)
        y = torch.FloatTensor(y_train).reshape(-1, 1).to(self.device)

        # Split into train/val
        n_val = int(len(X) * validation_split)
        X_train_t, X_val = X[:-n_val], X[-n_val:]
        y_train_t, y_val = y[:-n_val], y[-n_val:]

        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0

        for epoch in range(epochs):
            self.model.train()

            # Mini-batch training
            indices = torch.randperm(len(X_train_t))
            for i in range(0, len(X_train_t), batch_size):
                batch_indices = indices[i:i+batch_size]
                batch_X = X_train_t[batch_indices]
                batch_y = y_train_t[batch_indices]

                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val)
                val_loss = self.criterion(val_outputs, y_val)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Train Loss: {loss.item():.4f}, Val Loss: {val_loss.item():.4f}")

        return self.model

    def predict(self, X):
        """Make predictions"""
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            predictions = self.model(X_tensor)
        return predictions.cpu().numpy().flatten()

    def save(self, path):
        """Save model"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'input_dim': self.model.network[0].in_features
        }, path)

    def load(self, path):
        """Load model"""
        checkpoint = torch.load(path, map_location=self.device)

        # Get input_dim from checkpoint
        input_dim = checkpoint.get('input_dim', 78)

        # Reinitialize model with correct input_dim
        self.model = TabularNet(input_dim=input_dim).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])

        return self.model
