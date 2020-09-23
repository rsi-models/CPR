del /q /s build
call "make.bat" html
xcopy "build/html" /s "../docs" /y