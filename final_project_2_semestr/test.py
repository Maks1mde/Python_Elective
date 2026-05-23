import cv2
from pathlib import Path

# Замените на реальный путь к одной картинке
img = cv2.imread('files/generated_samples/sample_0235_count_7.png')
if img is None:
    print('Файл не найден, укажите правильный путь')
else:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    print('Размер:', img.shape)
    print('BGR (среднее):', img.mean(axis=(0,1)))
    print('H (оттенок) min/max:', hsv[:,:,0].min(), hsv[:,:,0].max())
    print('S (насыщ.) min/max:', hsv[:,:,1].min(), hsv[:,:,1].max())
    print('V (яркость) min/max:', hsv[:,:,2].min(), hsv[:,:,2].max())
    print()
    print('Фон (BGR среднее по углам):')
    corners = [img[0,0], img[0,-1], img[-1,0], img[-1,-1]]
    print(sum(corners)/4)
