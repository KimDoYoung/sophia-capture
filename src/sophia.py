import datetime
import sys
import os
import traceback
import cv2
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QFileDialog, 
                               QScrollArea, QVBoxLayout, QWidget, QToolBar, QPushButton, 
                               QTextEdit, QStatusBar, QHBoxLayout, QSplitter, QRubberBand, QSizePolicy, QMessageBox, QLineEdit)
from PySide6.QtGui import QPixmap, QImage, QFont, QIcon, QCursor, QAction
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from utils import PosUtil, RegionName, get_region, get_save_path


VERSION = "0.9"

def apply_monitor_scale(pos):
    """모니터 배율을 고려해 '물리 좌표'로 보정"""
    device_scale = QApplication.primaryScreen().devicePixelRatio()
    scaled_x = pos.x() * device_scale  # 🔥 곱하기
    scaled_y = pos.y() * device_scale  # 🔥 곱하기
    return scaled_x, scaled_y

class CustomLabel(QLabel):
    """ (요구사항 3) Rubber Band (점선 사각형) 구현 """
    def __init__(self, parent=None):
        print("SophiaCapture Initialized")  # 프로그램이 실행되었는지 확인
        super().__init__(parent)
        self.setMouseTracking(True)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)  
        self.rubber_band.setStyleSheet("border: 2px dashed red; background: rgba(255, 0, 0, 50);")
        self.start_pos = None
        self.parent_window = parent  

        if not hasattr(self.parent_window, "original_image"):
            print("Error: parent_window does not have 'original_image'")

    def mouseMoveEvent(self, event):
        if self.parent_window.original_image is None:
            return

        disp_x, disp_y = PosUtil.display_pos(event.position())
        image_x, image_y = PosUtil.image_pos(event.position(), self.parent_window.scale_factor)

        label_rect = self.rect()
        disp_x = max(0, min(disp_x, label_rect.width() - 1))
        disp_y = max(0, min(disp_y, label_rect.height() - 1))

        # 이미지 범위내에 있을 때만 좌표 표시
        if 0 <= image_x < self.parent_window.original_image.shape[1] and 0 <= image_y < self.parent_window.original_image.shape[0]:
            self.parent_window.display_status_message(image_x, image_y)
        # rubber band
        if self.rubber_band.isVisible():
            self.rubber_band.setGeometry(QRect(self.start_pos, QPoint(disp_x, disp_y)).normalized())


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and (self.parent_window.rect_capture_mode or self.parent_window.image_capture_mode):
            # 화면 표시용 좌표 얻기
            disp_x, disp_y = PosUtil.display_pos(event.position())
            self.start_pos = QPoint(disp_x, disp_y)

            # QLabel 경계 내로 조정
            label_rect = self.rect()
            self.start_pos.setX(max(0, min(self.start_pos.x(), label_rect.width() - 1)))
            self.start_pos.setY(max(0, min(self.start_pos.y(), label_rect.height() - 1)))

            # Rubber Band 초기화
            self.rubber_band.setGeometry(QRect(self.start_pos, QSize(1, 1)))
            self.rubber_band.show()
            self.rubber_band.update()

        if event.button() == Qt.LeftButton and self.parent_window.mark_mode:
            # 화면 표시용 좌표
            disp_x, disp_y = PosUtil.display_pos(event.position())

            # 화면 표시용 좌표 -> 원본 이미지 좌표 변환
            image_x, image_y = PosUtil.disp_to_image_pos(disp_x, disp_y, self.parent_window.scale_factor)

            # 마크 생성
            mark = QLabel("+", self)
            mark.setStyleSheet("color: red; font-size: 16px; font-weight: bold; text-align: center;")
            mark.setAttribute(Qt.WA_TransparentForMouseEvents)
            mark.setFixedSize(20, 20)

            # 저장된 image 좌표를 표시용 좌표로 변환해서 마크 위치 설정
            ui_x, ui_y = PosUtil.image_to_disp_pos(image_x, image_y, self.parent_window.scale_factor)
            mark.move(ui_x - 10, ui_y - 10)  # 중앙 정렬
            mark.show()

            # mark_list에 저장 (mark 객체 + image 좌표)
            self.parent_window.mark_list.append((mark, image_x, image_y))
            self.parent_window.info_text.append(f"-----> Point({image_x}, {image_y})")


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_pos and (self.parent_window.rect_capture_mode or self.parent_window.image_capture_mode):
            disp_x, disp_y = PosUtil.display_pos(event.position())
            end_pos = QPoint(disp_x, disp_y)

            label_rect = self.rect()
            end_pos.setX(max(0, min(end_pos.x(), label_rect.width() - 1)))
            end_pos.setY(max(0, min(end_pos.y(), label_rect.height() - 1)))

            # disp 좌표를 원본 이미지 좌표로 변환
            start_image_x, start_image_y = PosUtil.disp_to_image_pos(self.start_pos.x(), self.start_pos.y(), self.parent_window.scale_factor)
            end_image_x, end_image_y = PosUtil.disp_to_image_pos(end_pos.x(), end_pos.y(), self.parent_window.scale_factor)

            # 이제 원본 이미지 기준으로 잘라야 할 rectangle 생성
            selected_rect = QRect(QPoint(start_image_x, start_image_y), QPoint(end_image_x, end_image_y)).normalized()

            # 이 selected_rect를 원본 이미지에 적용
            self.parent_window.process_selection(selected_rect)

            self.rubber_band.hide()
            self.rubber_band.update()

    def update_mark_positions(self):
        """확대/축소 시 마크 위치 업데이트"""
        for mark_tuple in self.mark_list:
            mark, image_x, image_y = mark_tuple
            
            # 원본 이미지 좌표에서 현재 스케일로 UI 좌표 계산
            disp_x,disp_y = PosUtil.image_to_disp_pos(image_x, image_y, self.parent_window.scale_factor)
            
            # 마크 위치 업데이트
            mark.move(disp_x - 10, disp_y - 10)

class SophiaCapture(QMainWindow):
    def __init__(self):
        super().__init__()

        self.VERSION = VERSION  # 버전 정보 추가
        # 이미지 관련 변수
        self.original_image = None  # 원본 이미지
        self.displayed_image = None  # 확대/축소용 이미지
        self.scale_factor = 1.0

        self.mark_mode = False # on :클릭시 포인트에 + 표시
        self.cross_cursor_mode = False # on : 마우스 커서가 + 라인
        self.mark_list = []  # 저장된 마크 리스트 + 리스트
        #사용자 region그리기
        self.drawn_rect_label = None  # 사각형 표시용 QLabel
        self.last_drawn_region = None  # (x, y, w, h)        

        self.setWindowTitle(f"Sophia Capture v{self.VERSION}")  # 창 제목 설정

        base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 파일(sophia.py)의 절대 경로
        icon_path = os.path.join(base_dir, "sophia_capture.ico")  # 절대 경로로 변경        
        
        #  아이콘 파일이 존재하는지 확인
        if not os.path.exists(icon_path):
            print(f"Error: Icon file not found: {icon_path}")
        else:
            print(f"Icon Loaded: {icon_path}")        
        self.setWindowIcon(QIcon(icon_path))  # 같은 폴더에 있는 ico 파일 사용

        # (요구사항 1) 프로그램 실행 시 최대화 (showEvent에서 처리)
        self.is_first_show = True

        
        #  메뉴바 설정
        self.menu = self.menuBar()
        file_menu = self.menu.addMenu("File")
        
        #  Open 메뉴 (Ctrl+O 핫키 추가)
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")  #  Ctrl+O 단축키 추가
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)

        #  About 메뉴 추가
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_popup)
        file_menu.addAction(about_action)

        #  Separator(구분선) 추가
        file_menu.addSeparator()

        #  Quit 메뉴 추가 (Alt+F4 그대로 유지)
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Alt+F4")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        #  Action 메뉴 추가
        action_menu = self.menu.addMenu("Action")

        # Save info...
        save_info_action = QAction("Save info...", self)
        save_info_action.triggered.connect(self.save_info_to_file)
        action_menu.addAction(save_info_action)

        # Copy to clipboard
        copy_clipboard_action = QAction("Copy to clipboard", self)
        copy_clipboard_action.triggered.connect(self.copy_info_to_clipboard)
        action_menu.addAction(copy_clipboard_action)

        # Separator
        action_menu.addSeparator()

        # Clear info
        clear_info_action = QAction("Clear info", self)
        clear_info_action.triggered.connect(self.clear_info_text)
        action_menu.addAction(clear_info_action)

        # set save folder
        set_save_folder_action = QAction("Set Save Folder...", self)
        set_save_folder_action.setShortcut("F4")
        set_save_folder_action.triggered.connect(self.set_save_folder_dialog)
        action_menu.addAction(set_save_folder_action)  # ✅ 최하단에 추가        

        # set save folder
        explore_folder_action = QAction("Open Save Folder", self)
        explore_folder_action.setShortcut("F9")
        explore_folder_action.triggered.connect(self.explore_folder_action)
        action_menu.addAction(explore_folder_action)  # ✅ 최하단에 추가        


        # (요구사항 2) 툴바 설정
        self.toolbar = QToolBar("Toolbar")
        self.addToolBar(self.toolbar)

        self.prev_btn = QPushButton("⬅️")  # ← 이모지
        self.prev_btn.setToolTip("Previous Image")
        self.prev_btn.clicked.connect(self.load_prev_image)
        self.toolbar.addWidget(self.prev_btn)

        self.next_btn = QPushButton("➡️")  # → 이모지
        self.next_btn.setToolTip("Next Image")
        self.next_btn.clicked.connect(self.load_next_image)
        self.toolbar.addWidget(self.next_btn)        

        self.info_btn = QPushButton("Info")
        self.next_btn.setToolTip("display image regions")
        self.info_btn.clicked.connect(self.show_image_regions)
        self.toolbar.addWidget(self.info_btn)

        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.setToolTip("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.toolbar.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.setToolTip("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.toolbar.addWidget(self.zoom_out_btn)

        self.reset_zoom_btn = QPushButton("1:1")
        self.reset_zoom_btn.setToolTip("Reset Zoom")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.toolbar.addWidget(self.reset_zoom_btn)


        self.rect_capture_btn = QPushButton("Rectangle Capture")
        self.rect_capture_btn.setCheckable(True)
        self.rect_capture_btn.setToolTip("Capture a rectangular area")
        self.rect_capture_btn.clicked.connect(self.toggle_rectangle_capture)
        self.toolbar.addWidget(self.rect_capture_btn)

        self.image_capture_btn = QPushButton("Image Capture")
        self.image_capture_btn.setCheckable(True)
        self.image_capture_btn.clicked.connect(self.toggle_image_capture)
        self.image_capture_btn.setToolTip("Capture the region of image")
        self.toolbar.addWidget(self.image_capture_btn)
        # Mark 기능 버튼 추가
        self.mark_btn = QPushButton("Mark")
        self.mark_btn.setCheckable(True)
        self.mark_btn.clicked.connect(self.toggle_mark_mode)
        self.mark_btn.setToolTip("Mark the clicked position with +")
        self.toolbar.addWidget(self.mark_btn)
        self.add_toolbar_separator()

        # Mark-Clear 버튼 추가
        self.mark_clear_btn = QPushButton("Clear Marks")
        self.mark_clear_btn.clicked.connect(self.clear_marks)
        self.mark_clear_btn.setToolTip("Clear all marks")
        self.toolbar.addWidget(self.mark_clear_btn)

        # Cross-Cursor 버튼 추가
        self.cross_cursor_btn = QPushButton("Cross Cursor")
        self.cross_cursor_btn.setCheckable(True)
        self.cross_cursor_btn.clicked.connect(self.toggle_cross_cursor)
        self.toolbar.addWidget(self.cross_cursor_btn)        

        # seperator
        self.add_toolbar_separator()
        # 🔹 Region 입력창
        self.region_input = QLineEdit()
        self.region_input.setPlaceholderText("x,y,w,h")
        self.region_input.setFixedWidth(150)
        self.toolbar.addWidget(self.region_input)

        # 🔹 Draw 버튼
        self.draw_btn = QPushButton("Draw")
        self.draw_btn.clicked.connect(self.draw_custom_region)
        self.toolbar.addWidget(self.draw_btn)

        # 🔹 Remove 버튼
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_custom_region)
        self.toolbar.addWidget(self.remove_btn)        

        # (요구사항 2) 중앙 레이아웃 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QHBoxLayout(self.central_widget)  # 좌우 배치

        self.image_label = CustomLabel(self)
        self.image_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)  #  좌측 상단 고정
        self.image_label.setScaledContents(False) 
        self.image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  #  크기 자동 변경 방지

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(False)  #  QLabel 크기가 자동 변경되지 않도록 설정


        # (요구사항 6, 7) 정보 표시 영역 (사용자 입력 가능)
        self.info_text = QTextEdit()
        self.info_text.setFixedWidth(600)  
        self.info_text.setFont(QFont("Arial", 14))  

        # (요구사항 2) 가변적인 7:3 비율 유지
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.scroll_area)
        self.splitter.addWidget(self.info_text)
        self.splitter.setSizes([840, 600])  

        main_layout.addWidget(self.splitter)

        # (요구사항 1, 2) Status Bar 설정 (Zoom Factor 추가)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.mouse_pos_label = QLabel("X: 0, Y: 0 | Zoom: x1.0")
        self.mouse_pos_label.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel("")
        self.message_label = QLabel("Ready")

        self.status_bar.addWidget(self.mouse_pos_label, 2)
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addWidget(self.message_label, 3)

        # 이미지 관련 변수
        self.image = None
        self.pixmap = None
        self.rect_capture_mode = False
        self.image_capture_mode = False
        self.captured_images_count = 0

    def add_toolbar_separator(self):
        """ 툴바에 수직 구분선 추가 """
        separator = QWidget()
        separator.setFixedWidth(2)  # 두께 설정
        separator.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        separator.setStyleSheet("background-color: gray;")  # 색상 설정
        self.toolbar.addWidget(separator)

    def showEvent(self, event):
        """ (요구사항 1) 프로그램 시작 시 최대화 """
        if self.is_first_show:
            self.showMaximized()
            self.is_first_show = False

    def toggle_rectangle_capture(self):
        """Rectangle Capture 모드 ON/OFF"""
        self.rect_capture_mode = not self.rect_capture_mode

        if self.rect_capture_mode:
            # 다른 모드 OFF
            self.image_capture_mode = False
            self.mark_mode = False
            self.image_capture_btn.setChecked(False)
            self.mark_btn.setChecked(False)
            self.image_label.setCursor(Qt.ArrowCursor)
            self.status_label.setText("Rectangle Capture ON")
        else:
            self.status_label.setText("")

        self.rect_capture_btn.setChecked(self.rect_capture_mode)

    def toggle_image_capture(self):
        """Image Capture 모드 ON/OFF"""
        self.image_capture_mode = not self.image_capture_mode

        if self.image_capture_mode:
            # 다른 모드 OFF
            self.rect_capture_mode = False
            self.mark_mode = False
            self.rect_capture_btn.setChecked(False)
            self.mark_btn.setChecked(False)
            self.image_label.setCursor(Qt.ArrowCursor)
            self.status_label.setText("Image Capture ON")
        else:
            self.status_label.setText("")

        self.image_capture_btn.setChecked(self.image_capture_mode)


    def process_selection(self, rect):
        """ 선택된 영역을 원본 이미지 좌표로 변환 후 저장 """
        if self.original_image is None:
            print("Error: original_image is None")  # 디버깅 추가
            return  

        # 화면 좌표 → 원본 좌표 변환
        x = int(rect.left())
        y = int(rect.top())
        w = int(rect.width())
        h = int(rect.height())
    
        #  잘못된 크기 방지
        if w <= 0 or h <= 0:
            print(f"warning: 잘못된 선택 영역: width={w}, height={h}")
            return

        # 원본 이미지 기준으로 좌표 확인
        h_img, w_img, _ = self.original_image.shape
        if x < 0 or y < 0 or x + w > w_img or y + h > h_img or (w < 5 and h < 5):
            print("Error: Selection out of bounds")  # 선택 영역이 이미지 범위를 초과하는 경우
            return

        if self.image_capture_mode:
            save_path = get_save_path(self.save_folder, base_name= "image", ext="png") 
            cropped = self.original_image[y:y+h, x:x+w]
            #  비어있는 이미지 방지
            if cropped is None or cropped.size == 0:
                print("warning: 잘라낸 이미지가 비어있습니다.")
                return

            ext = ".png"
            ret, buffer = cv2.imencode(ext, cropped)
            if ret:
                buffer.tofile(save_path)  #  한글 경로 지원
                self.info_text.append(f"----->Region({x}, {y}, {w}, {h})")
                self.info_text.append(f"{save_path} saved")
                self.captured_images_count += 1
            else:
                print("warning: 이미지 인코딩 실패")


        elif self.rect_capture_mode:
            # 화면 좌표 기준 (정확한 값 출력)
            self.info_text.append("-----> ")
            self.info_text.append(f"Rectangle({x}, {y}, {x+w}, {y + h})")  # 오른쪽/아래쪽 좌표를 포함하도록
            self.info_text.append(f"Region({x}, {y}, {w}, {h})")  # 원본 이미지 기준

    def open_image(self):
        home_path = os.path.expanduser("~")
        default_folder = os.path.join(home_path, "사진")
        if not os.path.exists(default_folder):
            default_folder = os.path.join(home_path, "Pictures")

        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", default_folder, "Images (*.png *.jpg *.bmp)")
        if not file_path:
            print("Warning: No file selected")
            return

        self.open_process(file_path)    

    def open_process(self, file_path, change_save_folder=True):
        if not file_path or not os.path.exists(file_path):
            print("Error: File does not exist.")
            return

        self.loaded_file_path = file_path  
        image_array = np.fromfile(file_path, dtype=np.uint8)
        self.original_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if self.original_image is None:
            print(f"Error: Failed to load image {file_path}")
            return

        print(f"Image loaded: {file_path}, Size: {self.original_image.shape[1]}x{self.original_image.shape[0]}")
        self.displayed_image = self.original_image.copy()
        self.scale_factor = 1.0
        self.display_image()

        self.setWindowTitle(f"Sophia Capture v{self.VERSION} - {file_path}")

        if change_save_folder:
            home_path = os.path.expanduser("~")
            default_folder = os.path.join(home_path, "Pictures", "SophiaCapture")

            image_basename = os.path.basename(file_path)
            image_name, _ = os.path.splitext(image_basename)
            self.save_folder = os.path.join(default_folder, image_name)
            os.makedirs(self.save_folder, exist_ok=True)

        self.captured_images_count = 0
        self.message_label.setText(self.save_folder)


    def show_image_regions(self):
        """ Info 버튼 클릭 시 info_text에 Region 정보 출력 """
        if self.original_image is None:
            self.info_text.append(" 이미지가 로드되지 않았습니다.")
            return

        h, w, _ = self.original_image.shape
        base_region = (0, 0, w, h)
        self.info_text.append("-----> Image Region Info")
        self.info_text.append(f"loaded image path: : {self.loaded_file_path}")
        self.info_text.append(f"base_region = Region(0, 0, {w}, {h})")

        for region_name in RegionName:
            region = get_region(region_name, base_region)
            self.info_text.append(f"{region_name.name}_REGION = Region{region}")

    def reset_zoom(self):
        """ 이미지 원래 크기로 복원 """
        if self.original_image is None:
            return
        self.scale_factor = 1.0
        self.display_image()
        self.update_marks()

    def zoom_in(self):
        """ 이미지 확대 (QLabel 크기 업데이트 포함) """
        if self.original_image is None:
            print("Error: zoom_in() called but original_image is None")
            return

        self.scale_factor *= 1.2
        print(f"Zoom In: New Scale Factor = {self.scale_factor}")

        self.display_image()
        self.update_marks()

        #  QPixmap이 존재할 때만 QLabel 크기 조정
        if not self.pixmap.isNull():
            new_size = self.pixmap.size()
            self.image_label.resize(new_size)
            print(f"Zoom In: QLabel New Size = {new_size.width()}x{new_size.height()}")

        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.update()

    def zoom_out(self):
        """ 이미지 축소 (QLabel 크기 업데이트 포함) """
        if self.original_image is None:
            print("Error: zoom_out() called but original_image is None")
            return

        self.scale_factor /= 1.2
        print(f"Zoom Out: New Scale Factor = {self.scale_factor}")

        self.display_image()
        self.update_marks()

        #  QPixmap이 존재할 때만 QLabel 크기 조정
        if not self.pixmap.isNull():
            new_size = self.pixmap.size()
            self.image_label.resize(new_size)
            print(f"Zoom Out: QLabel New Size = {new_size.width()}x{new_size.height()}")

        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.update()

    def update_marks(self):
        """ 기존 마크 좌표를 현재 scale_factor에 맞게 변환 """
        for mark, image_x, image_y in self.mark_list:
            scaled_x, scaled_y = PosUtil.image_to_disp_pos(image_x, image_y, self.scale_factor)
            mark.move(scaled_x, scaled_y)

    def display_image(self):
        """ 확대/축소 적용하여 이미지 표시 (QPixmap 변환 오류 및 품질 완전 개선) """
        if self.original_image is None:
            print("Error: display_image() called but original_image is None")
            return

        h, w, ch = self.original_image.shape
        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)

        if new_w < 1:
            new_w = 1
        if new_h < 1:
            new_h = 1

        print(f"Resizing Image to: {new_w}x{new_h}")

        if self.scale_factor == 1.0:
            # 1:1 비율이면 원본 그대로 사용
            display_img = self.original_image
        else:
            # 확대/축소할 때만 resize
            display_img = cv2.resize(self.original_image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        self.displayed_image = display_img

        # BGR -> RGB 명시적 변환
        rgb_image = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)

        # QImage 생성 후 .copy() 호출로 메모리 완전 복사
        qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], rgb_image.strides[0], QImage.Format_RGB888).copy()

        # QPixmap 생성
        self.pixmap = QPixmap.fromImage(qt_image)

        if self.pixmap.isNull():
            print("Error: QPixmap conversion failed!")
            return

        print(f"Pixmap Created: {self.pixmap.width()}x{self.pixmap.height()}")

        # 화면 스케일 비율 감지
        scale_factor = self.devicePixelRatioF()

        # Pixmap에 스케일 적용
        self.pixmap.setDevicePixelRatio(scale_factor)

        self.image_label.setPixmap(self.pixmap)
        self.image_label.setScaledContents(False)
        self.image_label.resize(self.pixmap.size() / scale_factor)        

        #  QLabel 크기를 Pixmap 크기로 설정
        self.image_label.resize(self.pixmap.size())
        print(f"QLabel New Size: {self.image_label.width()}x{self.image_label.height()}")

        #  QScrollArea 업데이트
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.update()



    def display_status_message(self, x, y):
        """ (요구사항 1) 마우스 좌표 + Zoom Factor 업데이트 """
        self.mouse_pos_label.setText(f"X: {x}, Y: {y} | Zoom: x{self.scale_factor:.1f}")


    def show_about_popup(self):
        """ About 창을 표시하는 함수 """
        msg = QMessageBox(self)
        msg.setWindowTitle("About SophiaCapture")
        msg.setText(f"SophiaCapture v{self.VERSION}\n\nRPA용 이미지 잘라내기 및 위치 구하기 유틸리티\n\n© 2025 KimDoYoung")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)

        #  중앙 정렬
        msg.setStyleSheet("QLabel{ text-align: center; }")  
        msg.exec_()
#---------------------------------마크 기능 추가---------------------------------
    def clear_marks(self):
        """ 화면에 표시된 + 마크를 모두 삭제 """
        for mark, _, _ in self.mark_list:  # 🔹 튜플에서 QLabel(mark)만 가져오기
            mark.deleteLater()  # QLabel 제거
        self.mark_list.clear()  # 리스트 초기화

    def toggle_cross_cursor(self):
        """ Cross-Cursor 모드 ON/OFF """
        self.cross_cursor_mode = not self.cross_cursor_mode
        self.cross_cursor_btn.setChecked(self.cross_cursor_mode)

        if self.cross_cursor_mode:
            print("Cross Cursor ON")  
            cursor_pos = self.image_label.mapFromGlobal(QCursor.pos())  
            x = cursor_pos.x()
            y = cursor_pos.y()            
            self.image_label.update_mark_positions()  # 🔹 다시 그리기
            self.display_status_message()
        else:
            print(" Cross Cursor OFF: Removing lines")  
            self.remove_cross_cursor()  # 🔹 기존 수직/수평 라인 제거

    def remove_cross_cursor(self):
        """ 십자선 제거 """
        if hasattr(self.image_label, "h_line") and self.image_label.h_line:
            print("🛠 Removing horizontal line")
            self.image_label.h_line.deleteLater()
            self.image_label.h_line = None  # 🔹 참조 삭제

        if hasattr(self.image_label, "v_line") and self.image_label.v_line:
            print("🛠 Removing vertical line")
            self.image_label.v_line.deleteLater()
            self.image_label.v_line = None 
        
        self.image_label.update()  
        self.image_label.repaint()      

    def toggle_mark_mode(self):
        """Mark 모드 ON/OFF"""
        self.mark_mode = not self.mark_mode
        self.mark_btn.setChecked(self.mark_mode)

        if self.mark_mode:
            # 다른 모드 OFF
            self.rect_capture_mode = False
            self.image_capture_mode = False
            self.rect_capture_btn.setChecked(False)
            self.image_capture_btn.setChecked(False)
            self.status_label.setText("Mark Mode ON")
            self.image_label.setCursor(Qt.CrossCursor)
            print("Mark mode ON: Cursor changed to Cross")
        else:
            self.status_label.setText("")
            self.image_label.setCursor(Qt.ArrowCursor)
            print("Mark mode OFF: Cursor reset to Default")

    #------------------------------------------------------------------
    def save_info_to_file(self):
        """ info_text 내용을 파일로 저장 """
        text = self.info_text.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "Info", "저장할 내용이 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Info", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                QMessageBox.information(self, "Saved", f"{file_path} 저장 완료")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 저장 실패: {e}")

    def copy_info_to_clipboard(self):
        """ info_text 내용을 클립보드로 복사 """
        clipboard = QApplication.clipboard()
        clipboard.setText(self.info_text.toPlainText())
        QMessageBox.information(self, "Copied", "클립보드에 복사되었습니다.")

    def clear_info_text(self):
        """ info_text 내용 지우기 """
        self.info_text.clear()

    def set_save_folder_dialog(self):
        """ 폴더 선택 다이얼로그를 띄우고, 선택된 폴더를 저장 폴더로 설정 """
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.save_folder or "")
        if folder:
            self.save_folder = folder
            self.info_text.append(f"Save folder set to: {self.save_folder}")
            self.message_label.setText(self.save_folder)

    def explore_folder_action(self):
        ''' 선택된 저장 폴더를 탐색기에서 열기 '''
        if not self.save_folder:
            QMessageBox.warning(self, "Warning", "저장 폴더가 설정되지 않았습니다.")
            return
        if not os.path.exists(self.save_folder):
            QMessageBox.warning(self, "Warning", "저장 폴더가 존재하지 않습니다.")
            return
        os.startfile(self.save_folder)  # Windows에서 폴더 열기

#--------------------------------------------------------------------
    def load_prev_image(self):
        self.load_adjacent_image(-1)

    def load_next_image(self):
        self.load_adjacent_image(1)            

    def load_adjacent_image(self, direction):
        if not hasattr(self, "loaded_file_path") or not os.path.exists(self.loaded_file_path):
            return  # 이미지가 로드되지 않았으면 아무것도 하지 않음

        folder = os.path.dirname(self.loaded_file_path)
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not files:
            return

        full_paths = [os.path.join(folder, f) for f in files]
        sorted_files = sorted(full_paths, key=lambda f: os.path.getmtime(f))

        # 파일 이름 기준으로 현재 이미지 위치 찾기
        current_file_name = os.path.basename(self.loaded_file_path)
        current_index = next(
            (i for i, path in enumerate(sorted_files) if os.path.basename(path) == current_file_name),
            -1
        )
        if current_index == -1:
            return

        # 🔁 순환 처리
        new_index = (current_index + direction) % len(sorted_files)        
        self.open_process(sorted_files[new_index], change_save_folder=False)  # 저장 폴더 변경 안 함

#---------------------------------------------------------------
# 사용자 region 그리기
#---------------------------------------------------------------
    def draw_custom_region(self):
        """ 입력된 좌표(x,y,w,h)로 사각형을 표시 """
        if self.original_image is None:
            QMessageBox.warning(self, "경고", "이미지가 먼저 로드되어야 합니다.")
            return

        text = self.region_input.text().strip()

        try:
            x, y, w, h = PosUtil.extract_x_y_w_h(text) # map(int, text.split(","))
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "x,y,w,h 형식으로 입력하세요 (예: 100,200,50,50)")
            return

        if w <= 0 or h <= 0:
            QMessageBox.warning(self, "입력 오류", "너비와 높이는 양수여야 합니다.")
            return

        # 기존 사각형 제거
        self.remove_custom_region()

        # 좌상단/우하단 원본 이미지 좌표 → 표시용 좌표 변환
        ui_x1, ui_y1 = PosUtil.image_to_disp_pos(x, y, self.scale_factor)
        ui_x2, ui_y2 = PosUtil.image_to_disp_pos(x + w, y + h, self.scale_factor)

        disp_w = ui_x2 - ui_x1
        disp_h = ui_y2 - ui_y1

        self.drawn_rect_label = QLabel(self.image_label)
        self.drawn_rect_label.setGeometry(ui_x1, ui_y1, disp_w, disp_h)
        self.drawn_rect_label.setStyleSheet("border: 2px solid red;")
        self.drawn_rect_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.drawn_rect_label.show()
        print(f"사각형 표시됨: ({x}, {y}, {w}, {h})")

            
    def draw_region_from_last(self):
        """ 저장된 좌표로 사각형 다시 그림 (스케일 반영) """
        if not self.last_drawn_region:
            return

        x, y, w, h = self.last_drawn_region
        self.remove_drawn_region()

        disp_x, disp_y = PosUtil.image_to_disp_pos(x, y, self.scale_factor)
        disp_w = int(w * self.scale_factor)
        disp_h = int(h * self.scale_factor)

        self.drawn_rect_label = QLabel(self.image_label)
        self.drawn_rect_label.setGeometry(disp_x, disp_y, disp_w, disp_h)
        self.drawn_rect_label.setStyleSheet("border: 2px solid red;")
        self.drawn_rect_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.drawn_rect_label.show()

    def remove_custom_region(self):
        """ 그려진 사각형 제거 """
        if self.drawn_rect_label:
            self.drawn_rect_label.deleteLater()
            self.drawn_rect_label = None
            self.region_input.clear()  # 입력창 초기화
            self.last_drawn_region = None  # 마지막 그려진 영역 초기화
            print("사각형 제거됨")

if __name__ == "__main__":
    print("Starting SophiaCapture...")  # 프로그램 시작 확인

    app = QApplication(sys.argv)
    print("QApplication initialized.")  # QApplication 생성 확인

    try:
        editor = SophiaCapture()
        print("SophiaCapture instance created.")  # SophiaCapture 인스턴스 생성 확인

        editor.show()
        print("SophiaCapture window shown.")  # SophiaCapture UI 표시 확인

        sys.exit(app.exec())  # 이벤트 루프 실행
    except Exception as e:
        # 현재 시간 기준 로그 파일명 생성
        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%d_%H_%M_%S")
        log_dir = "C:/tmp"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"sophia_{timestamp}.log")

        # 로그 파일 저장
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("Unhandled Exception:\n\n")
            f.write(traceback.format_exc())

        # 콘솔에도 출력 (optional)
        print(f" 오류 발생! 로그 저장됨: {log_path}")
