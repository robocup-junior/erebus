@echo off

set arg1=%1
set arg2=%2
set arg3=%3

if "%arg1%"=="" (
    echo NO CONTROLLER FILE SET
    goto :usage
)
if "%arg2%"=="" (
    echo NO WEBOTS CLIENT IP ADDRESS SET
    goto :usage
)
if "%arg3%"=="" (
    echo NO WEBOTS CLIENT PORT SET
    goto :usage
)

echo Setting controller url: tcp://%arg2%:%arg3%/Erebus_Bot
set WEBOTS_CONTROLLER_URL=tcp://%arg2%:%arg3%/Erebus_Bot
python %arg1%

:end
    exit /b

:usage
    set "BAT_NAME=%~nx0"
    echo.
    echo USAGE:
    echo    %BAT_NAME% [EREBUS CONTROLLER FILE] [WEBOTS CLIENT IP ADDRESS] [WEBOTS CLIENT PORT]
    echo.
    echo DESCRIPTION:
    echo    EREBUS CONTROLLER FILE: The controller file to run in erebus
    echo    WEBOTS CLIENT IP ADDRESS: Webots client ip address (see webots console for socket its waiting on)
    echo    WEBOTS CLIENT PORT: Webots client port (see webots console for socket its waiting on)
    echo.
    goto :end