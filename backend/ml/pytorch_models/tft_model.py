"""
TEMPORAL FUSION TRANSFORMER (TFT) FOR SPORTS PREDICTION
Uses last 15 games as context for sequence modeling
"""
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

# Try to import pytorch_forecasting, fallback to simple implementation
try:
    from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
    TFT_AVAILABLE = True
except ImportError:
    TFT_AVAILABLE = False
    print("pytorch_forecasting not installed - using simplified TFT")


class SimpleTFT(nn.Module):
    """
    Simplified TFT implementation for when pytorch_forecasting unavailable
    Uses LSTM + Attention for sequence modeling
    """
    def __init__(self, input_dim=78, hidden_dim=64, num_layers=2, sequence_length=15):
        super().__init__()
        self.sequence_length = sequence_length
        
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=4, batch_first=True)
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        # x shape: [batch, sequence, features]
        lstm_out, _ = self.lstm(x)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        # Take last timestep
        final = attn_out[:, -1, :]
        return self.fc(final).squeeze(-1)


class SportsTFT:
    """
    Wrapper for TFT model training and prediction
    """
    def __init__(self, sequence_length=15, input_dim=78):
        self.sequence_length = sequence_length
        self.input_dim = input_dim
        
        if TFT_AVAILABLE:
            self.model = None  # Will be created from dataset
        else:
            self.model = SimpleTFT(input_dim=input_dim, sequence_length=sequence_length)
    
    def prepare_sequences(self, df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        """
        Convert game-by-game data to sequences
        Each prediction uses last N games as context
        """
        sequences = []
        for i in range(self.sequence_length, len(df)):
            seq = df[feature_cols].iloc[i-self.sequence_length:i].values
            sequences.append(seq)
        return np.array(sequences)
    
    def train(self, X_sequences, y):
        """Train the TFT model"""
        if not TFT_AVAILABLE:
            # Use simple implementation
            X_tensor = torch.FloatTensor(X_sequences)
            y_tensor = torch.FloatTensor(y)
            
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            criterion = nn.BCELoss()
            
            dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
            loader = torch.utils.data.DataLoader(dataset, batch_size=16, shuffle=True)
            
            self.model.train()
            for epoch in range(50):
                for batch_X, batch_y in loader:
                    optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
        
        return self
    
    def predict(self, X_sequences):
        """Generate predictions"""
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_sequences)
            return self.model(X_tensor).numpy()
    
    def save(self, path):
        torch.save(self.model.state_dict(), path)
    
    def load(self, path):
        self.model.load_state_dict(torch.load(path))
        return self


def train_tft(train_df: pd.DataFrame, feature_cols: List[str], target_col: str):
    """
    Full TFT training pipeline
    """
    if TFT_AVAILABLE:
        training = TimeSeriesDataSet(
            train_df,
            time_idx="game_idx",
            target=target_col,
            group_ids=["team"],
            max_encoder_length=15,
            max_prediction_length=1,
            static_categoricals=["home_team", "away_team"],
            time_varying_known_reals=feature_cols[:10],
            time_varying_unknown_reals=[target_col],
            target_normalizer=None,
        )
        tft = TemporalFusionTransformer.from_dataset(
            training, 
            learning_rate=1e-3, 
            hidden_size=64
        )
        return tft
    else:
        # Use simplified version
        sports_tft = SportsTFT(sequence_length=15, input_dim=len(feature_cols))
        sequences = sports_tft.prepare_sequences(train_df, feature_cols)
        y = train_df[target_col].values[15:]
        sports_tft.train(sequences, y)
        return sports_tft
