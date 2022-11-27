@echo off

IF "%WEBOTS_HOME%"=="" (
    echo WEBOTS_HOME not set
    set /p "webots_path=Enter your Webots installation path (e.g. C:\Program Files\Webots): "
    set WEBOTS_HOME=%webots_path%
    echo Set WEBOTS_HOME=%webots_path%
) ELSE (
    set /p "webots_path_set=WEBOTS_HOME already set (WEBOTS_HOME=%WEBOTS_HOME%), update it? (y/n): "
    IF %webots_path_set%==y (
        set /p "webots_path=Enter your Webots installation path (e.g. C:\Program Files\Webots): "
        set WEBOTS_HOME=%webots_path%
        echo Set WEBOTS_HOME=%webots_path%
    ) 
)

path|find /i "%WEBOTS_HOME%\lib\controller"         >nul || set path=%path%;%WEBOTS_HOME%\lib\controller
path|find /i "%WEBOTS_HOME%\msys64\mingw64\bin"     >nul || set path=%path%;%WEBOTS_HOME%\msys64\mingw64\bin
path|find /i "%WEBOTS_HOME%\msys64\mingw64\bin\cpp" >nul || set path=%path%;%WEBOTS_HOME%\msys64\mingw64\bin\cpp

IF "%PYTHONPATH%"=="" (
    set /p "python_ver=Enter Python (37, 38 or 39): "
    set path=%path%;%WEBOTS_HOME%\lib\controller\python%python_ver%
) ELSE (
    echo PYTHONPATH already set: %PYTHONPATH%
)

IF "%PYTHONIOENCODING%"=="" (
    set PYTHONIOENCODING=UTF-8
) ELSE (
    echo PYTHONIOENCODING already set: %PYTHONIOENCODING%
)

echo Erebus Remote Controller Environment Variables Set