"""
Обучение U-Net (ResNet18 encoder) для сегментации пятен.
"""
import cv2
import numpy as np
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from tqdm import tqdm
import os

NUM_WORKERS = min(os.cpu_count() or 1, 8)
BATCH_SIZE = 4  # U-Net тяжелее — меньше батч
torch.set_num_threads(os.cpu_count() or 4)


def create_mask(gray: np.ndarray) -> np.ndarray:
    """Бинарная маска пятен."""
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=3)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)
    return binary


class SegmentationDataset(Dataset):
    def __init__(self, data_dir: str, augment: bool = False):
        self.data_dir = Path(data_dir)
        self.paths = sorted(self.data_dir.glob("*.png"))
        self.augment = augment
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img = cv2.imread(str(self.paths[idx]))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        mask = create_mask(gray)

        h, w = img.shape[:2]
        new_h = ((h + 31) // 32) * 32
        new_w = ((w + 31) // 32) * 32
        img = cv2.resize(img, (new_w, new_h))
        mask = cv2.resize(mask, (new_w, new_h)) // 255

        if self.augment and np.random.rand() > 0.5:
            img = cv2.flip(img, 1)
            mask = cv2.flip(mask, 1)
        if self.augment and np.random.rand() > 0.5:
            img = cv2.flip(img, 0)
            mask = cv2.flip(mask, 0)

        return self.transform(img), torch.from_numpy(mask).float().unsqueeze(0), 0


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

        for name, param in backbone.named_parameters():
            if "layer3" in name or "layer4" in name:
                param.requires_grad = True
            else:
                param.requires_grad = False

        self.up4 = nn.ConvTranspose2d(512, 256, 2, 2)
        self.conv4 = DoubleConv(512, 256)

        self.up3 = nn.ConvTranspose2d(256, 128, 2, 2)
        self.conv3 = DoubleConv(256, 128)

        self.up2 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.conv2 = DoubleConv(128, 64)

        self.up1 = nn.ConvTranspose2d(64, 64, 2, 2)
        self.conv1 = DoubleConv(128, 64)

        self.up0 = nn.ConvTranspose2d(64, 32, 2, 2)
        self.conv0_fix = nn.Sequential(
            nn.Conv2d(32, 32, 3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
        )

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
        d0 = self.conv0_fix(d0)

        return self.final(d0)


def train(data_dir: str, epochs: int = 40):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device} | Workers: {NUM_WORKERS} | Batch: {BATCH_SIZE}")

    dataset = SegmentationDataset(data_dir, augment=True)
    split = int(len(dataset) * 0.85)
    train_ds, val_ds = torch.utils.data.random_split(dataset, [split, len(dataset) - split])

    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS, pin_memory=(device.type == 'cuda'),
        persistent_workers=True
    )
    val_loader = DataLoader(
        val_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=(device.type == 'cuda'),
    )

    model = UNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    criterion = nn.BCEWithLogitsLoss()

    best_loss = float("inf")
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for imgs, masks, _ in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
            imgs, masks = imgs.to(device), masks.to(device)
            pred = model(imgs)
            loss = criterion(pred, masks)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for imgs, masks, _ in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                val_loss += criterion(model(imgs), masks).item()

        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        scheduler.step(val_loss)

        lr = optimizer.param_groups[0]['lr']
        print(f"  loss: {train_loss:.4f}/{val_loss:.4f} | lr: {lr:.6f}")

        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), "models/unet_weights.pth")
            print(f"  ✓ Сохранена (val_loss={val_loss:.4f})")

    print(f"Готово: models/unet_weights.pth")


if __name__ == "__main__":
    import sys
    train(sys.argv[1] if len(sys.argv) > 1 else "files/generated_samples")