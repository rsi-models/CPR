del /q /s build
del /q /s "source/_build"
call "make.bat" html
xcopy "build/html" /s "../docs" /y