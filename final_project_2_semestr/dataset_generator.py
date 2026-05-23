"""
Генератор синтетических гистологических изображений.
"""
import os
import cv2
import numpy as np
import random
from pathlib import Path
from PIL import Image
import torchvision.transforms as transforms


def extract_patches(
    data_dir: str,
    output_dir: str,
    patch_size: int = 256,
    num_images: int = 0,
    cells_per_img: int = 4,
    bg_per_img: int = 4,
    cell_margin: int = 5
):
    """Извлечение патчей клеток и фона из реальных изображений."""
    bg_dir = os.path.join(output_dir, "bg_patches")
    cell_dir = os.path.join(output_dir, "cell_patches")
    os.makedirs(bg_dir, exist_ok=True)
    os.makedirs(cell_dir, exist_ok=True)

    original_dir = os.path.join(data_dir, "original")
    mask_dir = os.path.join(data_dir, "mask")

    if not os.path.exists(original_dir) or not os.path.exists(mask_dir):
        print(f"⚠ Директории не найдены: {original_dir} или {mask_dir}")
        return 0, 0

    img_dict = {p.stem: p for p in Path(original_dir).glob("*.png")}
    mask_dict = {p.stem: p for p in Path(mask_dir).glob("*.png")}
    common = sorted(set(img_dict.keys()) & set(mask_dict.keys()))

    if num_images > 0:
        common = common[:num_images]

    bg_saved, cell_saved = 0, 0

    for stem in common:
        img = cv2.imread(str(img_dict[stem]))
        mask = cv2.imread(str(mask_dict[stem]), cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            continue

        h, w = img.shape[:2]

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        valid_cells = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 150]
        random.shuffle(valid_cells)

        cell_found = 0
        for idx in valid_cells:
            if cell_found >= cells_per_img:
                break

            x, y, cw, ch = cv2.boundingRect((labels == idx).astype(np.uint8))
            x1 = max(0, x - cell_margin)
            y1 = max(0, y - cell_margin)
            x2 = min(w, x + cw + cell_margin)
            y2 = min(h, y + ch + cell_margin)

            sub_mask = mask[y1:y2, x1:x2].copy()
            _, _, sub_stats, _ = cv2.connectedComponentsWithStats(sub_mask, connectivity=8)
            if sum(1 for k in range(1, len(sub_stats)) if sub_stats[k, cv2.CC_STAT_AREA] >= 150) != 1:
                continue

            patch = img[y1:y2, x1:x2].copy()
            patch[sub_mask == 0] = 0
            cv2.imwrite(os.path.join(cell_dir, f"cell_{cell_saved:05d}.png"), patch)
            cell_saved += 1
            cell_found += 1

        bg_found = 0
        attempts = 0
        while bg_found < bg_per_img and attempts < 300:
            y = random.randint(0, max(0, h - patch_size))
            x = random.randint(0, max(0, w - patch_size))
            p_mask = mask[y:y+patch_size, x:x+patch_size]
            if np.sum(p_mask > 0) == 0:
                p_img = img[y:y+patch_size, x:x+patch_size].copy()
                cv2.imwrite(os.path.join(bg_dir, f"bg_{bg_saved:05d}.png"), p_img)
                bg_saved += 1
                bg_found += 1
            attempts += 1

    return bg_saved, cell_saved


class BloodCellDataset:
    """Датасет синтетических изображений с пятнами."""

    def __init__(
        self,
        bg_dir: str = "",
        cell_dir: str = "",
        img_size: tuple = (256, 256),
        dataset_size: int = 1500,
        max_cells: int = 8,
    ):
        self.img_size = img_size
        self.dataset_size = dataset_size
        self.max_cells = max_cells

        self.bg_paths = list(Path(bg_dir).glob("*.png")) if bg_dir and os.path.exists(bg_dir) else []
        self.cell_paths = list(Path(cell_dir).glob("*.png")) if cell_dir and os.path.exists(cell_dir) else []
        self.has_bg = len(self.bg_paths) > 0
        self.has_cells = len(self.cell_paths) > 0

    def __len__(self):
        return self.dataset_size

    def _synth_bg(self):
        color = np.random.randint(200, 250, 3)
        bg = np.full((self.img_size[1], self.img_size[0], 3), color, dtype=np.uint8)
        noise = np.random.normal(0, 8, bg.shape).astype(np.int16)
        return np.clip(bg.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    def _synth_cell(self):
        size = random.randint(15, 45)
        cell = np.zeros((size, size, 3), dtype=np.uint8)
        center = (size // 2, size // 2)
        # Тёмное пятно
        color = (
            random.randint(30, 100),
            random.randint(20, 60),
            random.randint(20, 60),
        )
        cv2.circle(cell, center, size // 2 - 2, color, -1)
        noise = np.random.normal(0, 5, cell.shape).astype(np.int16)
        cell = np.clip(cell.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        cell = cv2.GaussianBlur(cell, (5, 5), 0.8)
        return cell

    def __getitem__(self, idx):
        # Фон
        if self.has_bg and random.random() > 0.3:
            canvas = cv2.resize(cv2.imread(str(random.choice(self.bg_paths))), self.img_size)
        else:
            canvas = self._synth_bg()

        # Наложение пятен
        num_cells = random.randint(0, self.max_cells)
        for _ in range(num_cells):
            if self.has_cells and random.random() > 0.4:
                cell = cv2.imread(str(random.choice(self.cell_paths)))
                scale = random.uniform(0.4, 1.0)
                cell = cv2.resize(cell, (int(cell.shape[1] * scale), int(cell.shape[0] * scale)))
            else:
                cell = self._synth_cell()

            h, w = cell.shape[:2]
            x = random.randint(0, max(0, self.img_size[0] - w))
            y = random.randint(0, max(0, self.img_size[1] - h))

            gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
            mask = mask.astype(np.float32) / 255.0
            mask_3d = np.stack([mask] * 3, axis=-1)

            roi = canvas[y:y+h, x:x+w].astype(np.float32)
            blended = roi * (1 - mask_3d) + cell.astype(np.float32) * mask_3d
            canvas[y:y+h, x:x+w] = np.clip(blended, 0, 255).astype(np.uint8)

        # Постобработка
        noise = np.random.normal(0, 5, canvas.shape).astype(np.int16)
        canvas = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        canvas = cv2.GaussianBlur(canvas, (3, 3), 0.5)

        return canvas, num_cells


def generate_dataset(
    output_dir: str,
    num_samples: int = 1500,
    img_size: tuple = (256, 256),
    max_cells: int = 8,
    bg_dir: str = "",
    cell_dir: str = "",
    progress_callback=None,
):
    """
    Генерация датасета.

    Args:
        output_dir: куда сохранять
        num_samples: количество изображений
        img_size: размер (ширина, высота)
        max_cells: максимальное число пятен
        bg_dir: папка с фоновыми патчами (опционально)
        cell_dir: папка с патчами клеток (опционально)
        progress_callback: функция(процент) для обновления прогресса
    """
    os.makedirs(output_dir, exist_ok=True)

    dataset = BloodCellDataset(
        bg_dir=bg_dir,
        cell_dir=cell_dir,
        img_size=img_size,
        dataset_size=num_samples,
        max_cells=max_cells,
    )

    for i in range(num_samples):
        img, count = dataset[i]
        img_path = os.path.join(output_dir, f"sample_{i:04d}_count_{count}.png")
        cv2.imwrite(img_path, img)

        if progress_callback and i % 50 == 0:
            progress_callback(int((i + 1) / num_samples * 100))

    # Сохраняем targets.csv
    targets_path = os.path.join(output_dir, "targets.csv")
    with open(targets_path, "w") as f:
        f.write("filename,count\n")
        for p in sorted(Path(output_dir).glob("sample_*.png")):
            import re
            match = re.search(r'_count_(\d+)', p.name)
            if match:
                f.write(f"{p.name},{match.group(1)}\n")

    return output_dir