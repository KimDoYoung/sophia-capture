from enum import Enum
import os
import re
from typing import Optional, Tuple
from PySide6.QtWidgets import QApplication

class RegionName(Enum):
    LEFT_ONE_THIRD = 1
    RIGHT_ONE_THIRD = 2
    TOP_ONE_THIRD = 3
    BOTTOM_ONE_THIRD = 4
    LEFT_TOP = 5
    RIGHT_TOP = 6
    RIGHT_BOTTOM = 7
    LEFT_BOTTOM = 8
    CENTER = 9
    LEFT = 10
    RIGHT = 11
    TOP = 12
    BOTTOM = 13

def get_region(region_name: RegionName, base_region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[int, int, int, int]:

    left, top, width, height = base_region

    if region_name == RegionName.LEFT_ONE_THIRD:
        return (left, top, width // 3, height)
    elif region_name == RegionName.RIGHT_ONE_THIRD:
        return (left + 2 * (width // 3), top, width // 3, height)
    elif region_name == RegionName.TOP_ONE_THIRD:
        return (left, top, width, height // 3)
    elif region_name == RegionName.BOTTOM_ONE_THIRD:
        return (left, top + 2 * (height // 3), width, height // 3)
    elif region_name == RegionName.LEFT_TOP:
        return (left, top, width // 2, height // 2)
    elif region_name == RegionName.RIGHT_TOP:
        return (left + width // 2, top, width // 2, height // 2)
    elif region_name == RegionName.RIGHT_BOTTOM:
        return (left + width // 2, top + height // 2, width // 2, height // 2)
    elif region_name == RegionName.LEFT_BOTTOM:
        return (left, top + height // 2, width // 2, height // 2)
    elif region_name == RegionName.CENTER:
        return (left + width // 3, top + height // 3, width // 3, height // 3)
    elif region_name == RegionName.LEFT:
        return (left, top, width // 2, height)
    elif region_name == RegionName.RIGHT:
        return (left + width // 2, top, width // 2, height)
    elif region_name == RegionName.TOP:
        return (left, top, width, height // 2)
    elif region_name == RegionName.BOTTOM:
        return (left, top + height // 2, width, height // 2)
    else:
        raise ValueError("잘못된 RegionName 값입니다.")
    
def get_save_path(folder_path, base_name="image", ext=".png"):
    """중복되지 않는 저장 경로를 반환한다.
    
    Args:
        folder_path (str): 저장할 폴더 경로
        base_name (str): 파일 이름 기본값 (예: "image")
        ext (str): 확장자 (예: ".png")

    Returns:
        str: 저장할 파일 전체 경로
    """
    count = 0
    while True:
        filename = f"{base_name}_{count}.{ext}"
        save_path = os.path.join(folder_path, filename)
        if not os.path.exists(save_path):
            return save_path
        count += 1    

class PosUtil:
    @staticmethod
    def display_pos(pos):
        """화면 표시용 좌표 반환 (UI 좌표 그대로)"""
        return int(pos.x()), int(pos.y())

    @staticmethod
    def image_pos(pos, scale_factor):
        """원본 이미지 좌표 반환 (DPI 보정 + 배율 보정)"""
        device_scale = QApplication.primaryScreen().devicePixelRatio()
        phys_x = pos.x() * device_scale
        phys_y = pos.y() * device_scale
        image_x = int(phys_x / scale_factor)
        image_y = int(phys_y / scale_factor)
        return image_x, image_y

    @staticmethod
    def disp_to_image_pos(disp_x, disp_y, scale_factor):
        """화면 표시용 좌표 -> 원본 이미지 좌표 변환"""
        device_scale = QApplication.primaryScreen().devicePixelRatio()
        phys_x = disp_x * device_scale
        phys_y = disp_y * device_scale
        image_x = int(phys_x / scale_factor)
        image_y = int(phys_y / scale_factor)
        return image_x, image_y

    @staticmethod
    def image_to_disp_pos(image_x, image_y, scale_factor):
        """원본 이미지 좌표 -> 화면 표시용 좌표 변환"""
        device_scale = QApplication.primaryScreen().devicePixelRatio()
        disp_x = int(image_x * scale_factor / device_scale)
        disp_y = int(image_y * scale_factor / device_scale)
        return disp_x, disp_y

    @staticmethod
    def extract_x_y_w_h(text: str) -> tuple[int, int, int, int]:
        """
        문자열에서 (x, y, w, h) 형태의 Region 정보를 추출하여 반환
        - Region(1,2,3,4) → (1,2,3,4)
        - Rectangle(1,2,3,4) → (x, y, w=x2-x, h=y2-y)
        - 1,2,3,4 → (1,2,3,4)
        """
        numbers = re.findall(r"\d+", text)
        if len(numbers) != 4:
            raise ValueError("숫자 4개가 포함된 문자열이 아닙니다.")

        x1, y1, x2, y2 = map(int, numbers)

        if "rectangle" in text.lower():
            x = x1
            y = y1
            w = x2 - x1
            h = y2 - y1
            if w <= 0 or h <= 0:
                raise ValueError("Rectangle 좌표가 올바르지 않습니다.")
            return (x, y, w, h)

        return (x1, y1, x2, y2)