import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
from .algorithm_plugin import AlgorithmMeta


class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)


class UNet(nn.Module):
    """U-Net с ResNet18 энкодером."""
    def __init__(self):
        super().__init__()
        from torchvision.models import resnet18, ResNet18_Weights
        backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

        self.enc0 = nn.Sequential(backbone.conv1, backbone.bn1, backbone.relu)
        self.pool = backbone.maxpool
        self.enc1 = backbone.layer1
        self.enc2 = backbone.layer2
        self.enc3 = backbone.layer3
        self.enc4 = backbone.layer4

        self.up4 = nn.ConvTranspose2d(512, 256, 2, 2)
        self.conv4 = DoubleConv(512, 256)

        self.up3 = nn.ConvTranspose2d(256, 128, 2, 2)
        self.conv3 = DoubleConv(256, 128)

        self.up2 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.conv2 = DoubleConv(128, 64)

        self.up1 = nn.ConvTranspose2d(64, 64, 2, 2)
        self.conv1 = DoubleConv(128, 64)

        self.up0 = nn.ConvTranspose2d(64, 32, 2, 2)
        self.conv0 = DoubleConv(64, 32)

        self.final = nn.Conv2d(32, 1, 1)

    def forward(self, x):
        e0 = self.enc0(x)
        e0p = self.pool(e0)
        e1 = self.enc1(e0p)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)

        d4 = self.up4(e4)
        d4 = torch.cat([d4, e3], dim=1)
        d4 = self.conv4(d4)

        d3 = self.up3(d4)
        d3 = torch.cat([d3, e2], dim=1)
        d3 = self.conv3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, e1], dim=1)
        d2 = self.conv2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e0], dim=1)
        d1 = self.conv1(d1)

        d0 = self.up0(d1)
        d0 = torch.cat([d0, x], dim=1)
        d0 = self.conv0(d0)

        return self.final(d0)


class UNetModel(AlgorithmMeta, algorithm_name="unet"):
    """
    Подсчёт пятен: U-Net + ResNet18 encoder.
    """

    def __init__(
        self,
        model_path: str | None = "models/unet_weights.pth",
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
        self.model: UNet | None = None

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    def get_name(self) -> str:
        return "U-Net (ResNet18 encoder)"

    def _load_model(self):
        model = UNet().to(self.device)
        if self.model_path:
            try:
                state_dict = torch.load(self.model_path, map_location=self.device, weights_only=True)
                model.load_state_dict(state_dict)
            except FileNotFoundError:
                pass  # Веса не найдены — используем без обучения
        model.eval()
        return model

    def count_cells(self, image: np.ndarray) -> int:
        if self.model is None:
            self.model = self._load_model()

        orig_h, orig_w = image.shape[:2]
        pad_h = (32 - orig_h % 32) % 32
        pad_w = (32 - orig_w % 32) % 32
        padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)

        tensor = self.transform(padded).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            mask = torch.sigmoid(logits).squeeze().cpu().numpy()

        mask = mask[:orig_h, :orig_w]
        binary = (mask > self.threshold).astype(np.uint8) * 255

        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        count = 0
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if self.min_area <= area <= self.max_area:
                count += 1

        return count

    def get_mask(self, image: np.ndarray) -> np.ndarray:
        if self.model is None:
            self.model = self._load_model()

        orig_h, orig_w = image.shape[:2]
        pad_h = (32 - orig_h % 32) % 32
        pad_w = (32 - orig_w % 32) % 32
        padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)

        tensor = self.transform(padded).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            mask = torch.sigmoid(logits).squeeze().cpu().numpy()

        mask = mask[:orig_h, :orig_w]
        return (mask > self.threshold).astype(np.uint8) * 255