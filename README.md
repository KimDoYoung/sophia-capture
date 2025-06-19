# sophia-capture

## 개요

- [kavana](https://github.com/KimDoYoung/kavana)(RPA용 Script) 프로젝트를 위한 유틸리티
- kavana script에서 사용할 이미지 또는 region, point등을 구하기 위한 GUI 프로그램
- 이미지에서 region이나 rectangle을 구함
- 이미지에서 영역을 선택해서 이미지를 잘라내어 저장함.
- zoonin(확대)을 해서 영역을 잘라냄, 원래의 이미지 크기로 잘라냄

## 설치

```bash
make.sh
```
- dist 폴더에 sophia.exe가 만들어짐.

## History

- 0.2 : 2025-04-16 한글이미지 파일명 저장 안되는 것 수정, Action 메뉴추가
- 0.3 : kavana code 스타일로 point, region등 출력
- 0.4 : PySide6로 변경함.
- 0.5 : scale버그 수정, F4: set save folder 메뉴추가
- 0.6 : next image, prev image 버튼 생성, info에 file full path 넣기.
- 0.7 : next,prev image변경시 save_folder 유지, F9 : save_folder 탐색기에서 열기
- 0.8 : zoom in추가, 사용자 region그리기
- 0.9 : image자를때 region도 표시, w,h < 10pixel이하는 무시함.