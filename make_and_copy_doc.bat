del /q /s build
call "./docsrc/make.bat" html
xcopy "./docsrc/build/html" /s "./docs" /y