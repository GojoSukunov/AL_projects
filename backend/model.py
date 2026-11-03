
import torch
import torch.nn as nn
from pathlib import Path


# Архитектура из твоего CIFAR.ipynb
class CifarClassification(nn.Module):

    def __init__(self):
        super().__init__()

        self.first = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.second = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU(),
            nn.Linear(256, 10)
        )

    def forward(self, image):
        image = self.first(image)
        image = self.second(image)
        return image


# Путь к файлу модели
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "model_CIFAR_ai32.pth"


def load_model():

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    model = CifarClassification().to(device)

    try:
        weights = torch.load(
            MODEL_PATH,
            map_location=device,
            weights_only=True
        )
    except TypeError:
        weights = torch.load(
            MODEL_PATH,
            map_location=device
        )

    model.load_state_dict(weights)
    model.eval()

    print("CIFAR-10 модель успешно загружена!")
    print("Устройство:", device)

    return model, device
