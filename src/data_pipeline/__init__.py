"""
Thermal Data Training Pipeline

PyTorch custom Dataset and DataLoader for thermal sensor data with annotations.
Fetches data directly from TDengine into memory for training.
"""

from .thermal_dataset import ThermalAnnotationDataset, create_dataloader

__version__ = "1.0.0"
__all__ = [
    "ThermalAnnotationDataset",
    "create_dataloader",
]

