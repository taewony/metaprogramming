import pygame

def preprocess_image(surface):
    """
    이미지 전처리:
    1. 가로 혹은 세로가 500 이상이면 비율을 유지하며 가장 긴 변을 200으로 리사이징.
    2. RGB 값이 모두 240 이상인 픽셀을 순수 흰색(255, 255, 255)으로 변환.
    """
    # 1. 리사이징 처리
    w, h = surface.get_size()
    if max(w, h) >= 500:
        if w > h:
            new_w = 200
            new_h = int(h * (200 / w))
        else:
            new_h = 200
            new_w = int(w * (200 / h))
        
        # smoothscale은 이미지 품질을 유지하며 크기를 조절함
        surface = pygame.transform.smoothscale(surface, (new_w, new_h))
    
    # 2. 흰색 정규화 (RGB > 240 -> 255)
    # 픽셀 배열을 직접 다루기 위해 PixelArray 사용
    pixel_array = pygame.PixelArray(surface)
    
    # Surface의 너비와 높이를 다시 가져옴 (리사이징 되었을 수 있으므로)
    sw, sh = surface.get_size()
    
    for x in range(sw):
        for y in range(sh):
            # 픽셀의 RGB 값 추출
            color = surface.unmap_rgb(pixel_array[x, y])
            if color.r > 240 and color.g > 240 and color.b > 240:
                pixel_array[x, y] = (255, 255, 255)
    
    # PixelArray 사용 완료 후 반드시 삭제하여 Surface 잠금 해제
    del pixel_array
    
    return surface
