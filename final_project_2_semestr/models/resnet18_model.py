import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights
from .algorithm_plugin import AlgorithmMeta


class ResNet18Segmentation(nn.Module):
    """ResNet18 для сегментации пятен."""

    def __init__(self):
        super().__init__()
        backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

        self.encoder = nn.Sequential(
            backbone.conv1, backbone.bn1, backbone.relu,
            backbone.maxpool, backbone.layer1, backbone.layer2,
            backbone.layer3, backbone.layer4,
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(512, 256, 4, 2, 1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.ConvTranspose2d(256, 128, 4, 2, 1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 4, 2, 1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.ConvTranspose2d(32, 16, 4, 2, 1), nn.BatchNorm2d(16), nn.ReLU(),
            nn.Conv2d(16, 1, 1),
        )

    def forward(self, x):
        features = self.encoder(x)
        return self.decoder(features)


class ResNet18Model(AlgorithmMeta, algorithm_name="resnet18"):
    """
    Подсчёт пятен: ResNet18 для сегментации + подсчёт компонент.
    """

    def __init__(
        self,
        model_path: str | None = None,
        device: str | None = None,
        threshold: float = 0.5,
        min_area: int = 30,
        max_area: int = 20000,
    ):
        self.model_path = model_path
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.threshold = threshold
        self.min_area = min_area
        self.max_area = max_area
        self.model: ResNet18Segmentation | None = None

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    def get_name(self) -> str:
        return "ResNet18 (сегментация)"

    def _load_model(self):
        model = ResNet18Segmentation().to(self.device)
        if self.model_path:
            state_dict = torch.load(self.model_path, map_location=self.device, weights_only=True)
            model.load_state_dict(state_dict)
        model.eval()
        return model

    def count_cells(self, image: np.ndarray) -> int:
        if self.model is None:
            self.model = self._load_model()

        orig_h, orig_w = image.shape[:2]

        # Паддинг до кратного 32
        pad_h = (32 - orig_h % 32) % 32
        pad_w = (32 - orig_w % 32) % 32
        padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)

        tensor = self.transform(padded).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            mask = torch.sigmoid(logits).squeeze().cpu().numpy()

        # Обрезаем паддинг
        mask = mask[:orig_h, :orig_w]

        # Бинаризация
        binary = (mask > self.threshold).astype(np.uint8) * 255

        # Морфология — как в KNN
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)

        # Подсчёт
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        count = 0
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if self.min_area <= area <= self.max_area:
                count += 1

        return count