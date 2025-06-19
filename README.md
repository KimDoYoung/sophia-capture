# sophia_capture

## 개요

- RPA 프로젝트를 위한 유틸리티
- 이미지에서 region이나 rectangle을 구함
- 이미지에서 영역을 선택해서 이미지를 잘라내어 저장함.
- zoonin(확대)을 해서 영역을 잘라냄, 원래의 이미지 크기로 잘라냄

## 프롬프트

근래 RPA 프로그램을 주로 개발하는데,
주로 pyautogui를 사용하고 있음.
그런데 이미지 유틸리티가 필요하지 않나 생각이 듬, GUI프로그램임

주요 기능은 다음과 같음
대상 프로그램의 화면캡쳐를 한 후 저장된 이미지 -> batang.png 이 있다고 가정

### gui

1. top menu : file  open
2. toolbar : thumb-buttons
3. main : image영역과 정보영역으로 7:3의 비율을 갖음, 정보영역은 text표시할 수 있으면 됨
4. status bar : 하단에 간단정보표시

### 기능

1. batang.png을 open (이미지 open)-> 이미지가 화면에 나옴. scrollbar로 이미지 안보이는 부분 이동.
2. zoomin button클릭->화면커짐.
3. 1:1버튼 클릭 ->원래 이미지 크기로 돌아옴.
4. rectangle버튼 클릭, rectangle_ capture상태가 됨
5. rectangle_capture상태에서 마우스 클릭 후 드래그 후 마우스 up 시 선택된 rectangle(region) 을 정보영역에 표시
6. retangle_capture버튼 클릭 -> rectangle_capture  toggle
7. image_capture 버튼클릭 , image_cpautre 상태가 됨
8. image_capture 상태에서  우스 클릭 후 드래그 후 마우스 up 시 선택된 영역의 이미지를 저장 (이름은 자동으로 숫자증가 예를 들어 image_1.png, image_2.png식으로
9. image_capture 버튼 클릭 -> image_capture상태 toggle

### 1차 추가 요구사항

1. 요구조건 1
    status영역을 3부분으로 나누어서
    - 마우스의 x, y표시
    - 현재의 상태 즉 rectangle capture on 또는 image capture on을 표시, 물론 아무 상태도 아니면 비어 있게금.
    - 메세지 표시

2. 요구조건2
    - 정보영역의 넓기가 너무 작음 지금 사이즈의 2배로

3. 요구조건3
    - rectangle_capture on 또는 image_capture on일때 rubber band형식으로 점선으로 표시해 줄 수 없나?

### 2차 추가 요구사항

요구조건 1
File
    Open
    --------
    Config
    --------
    Quit(alt+f4)

요구조건 2
-Config menu click시 modal로 환경설정 모달창 뜰 것
-config-modal에서
-이미지 저장위치를 설정하게 할 것
-default 이미지 저장장치는 실행위치아래 images폴더를 만들것

1. 이미지 저장시 -> 정보영역에 'image_0.png' saved 표시
2. 초기상태 maxize
3. rectange_capture on 하면 image_catpure off  반대로 image_capture on 이면 rectange_capture off
4. 정보영역 font 더 크게

### 3차 요구사항

- status바의 x,y 마우스 위치를 중앙정렬
- status바에 zoom factor를 x,y 마우스 위치 뒤에 추가
- rectange-capture on 시 마우스 up 했었을 때 정보영역에 region이 안 나옴(버그)
- image_capture on시에도 마찬가지로 마우스 up했었을때 이미지가 저장되지 않음. (버그)
- image_capture on시 마우스 up했었을 때 이미지를 저장하고 그 파일명을 정보영역에 나오게끔.
- 정보영역의 font를 조금 더 크게
- 정보영역에 사용자가 입력할 수 있게 (region에 대해서 사용자가 설명을 넣기를 원함)
- 프로그램 시작시 윈도우를 최대로 하는 것 동작하지 않음 확인요망

### 추가요구사항 4차

- 프로그램 수행시 최대화 안됨(확인요망)
- region은 x,y,width,height임 지금은 두개의 point를 표현하고 있음.
  그래서
  mouse_release했을 때 rect :(x1,y1)-(x2,y2)
                     region : (x,y,w,h) 로 2줄로 표현해줘
- rectange_capture on 하면 image_catpure off  반대로 image_capture on 이면 rectange_capture off

### 추가요구사항 5차

- open 핫키 ctrl+o 추가
- about 메뉴 추가 클릭시  중앙에 팝업으로 간단 메세지
- about 다음에 sperator 라인
- Quit는 그대로

- 파일 오픈성공시 $HOME\사진\sophia_capture 하위에 오픈한 이미지파일명 (abc.png)으로 폴더생성 (있으면 skip)
- capture한 이미지번호를 0번부터 다시 시작
- 저장폴더명을 Ready 즉 statusbar 마지막 label에 표시

### 추가요구사항 6차

- 상단의 툴바에 3개의 버튼을 추가
    1.mark : 클릭시 mark-on = not makr-on으로 mark-on일때 마우스 클릭하는 곳마다. +를 표시 빨간색으로
    2.mark-clear : 클릭시 화면에 표시된 +를 모두 지움.
    3.cross-cursor : on일때 커서가 움직일때마다 horizontal line과 vertical line으로
    즉 이미지 전체 넓이와 이미지 전체 높이로 cross라인을 그리면서 마우스가 움직이도록
    on일때 다시 누르면 off

## History

0.2 : 2025-04-16 한글이미지 파일명 저장 안되는 것 수정, Action 메뉴추가
0.3 : kavana code 스타일로 point, region등 출력
0.4 : PySide6로 변경함.
0.5 : scale버그 수정, F4: set save folder 메뉴추가
0.6 : next image, prev image 버튼 생성, info에 file full path 넣기.
0.7 : next,prev image변경시 save_folder 유지, F9 : save_folder 탐색기에서 열기
0.8 : zoom in추가, 사용자 region그리기
0.9 : image자를때 region도 표시, w,h < 10pixel이하는 무시함.