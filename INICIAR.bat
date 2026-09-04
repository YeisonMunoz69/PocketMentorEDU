@echo off
chcp 65001 >nul
title Pocket Mentor EDU

echo.
echo =====================================================
echo   POCKET MENTOR EDU
echo =====================================================
echo.

SET BASE_DIR=%~dp0
SET PYTHON=%BASE_DIR%engine\python\python.exe
SET SETUP_FLAG=%BASE_DIR%engine\.setup_done
SET APP=%BASE_DIR%app\main.py

REM -- Verificar Python portable ---------------------------------------------
IF NOT EXIST "%PYTHON%" (
    echo [ERROR] Python portable no encontrado en engine\python\
    echo.
    echo La USB no esta correctamente preparada.
    echo Contacta al administrador del proyecto.
    pause
    exit /b 1
)

REM -- Verificar modelo LLM --------------------------------------------------
SET MODEL_COUNT=0
FOR %%F IN ("%BASE_DIR%models\*.gguf") DO SET /A MODEL_COUNT+=1
IF %MODEL_COUNT%==0 (
    echo [ERROR] No se encontro ningun modelo .gguf en models\
    echo.
    echo La USB no esta correctamente preparada.
    echo Contacta al administrador del proyecto.
    pause
    exit /b 1
)

REM -- Primera vez: verificar paquetes en WinPython bundled -----------------
IF NOT EXIST "%SETUP_FLAG%" (
    echo [INFO] Primera ejecucion — verificando paquetes incluidos...
    echo.

    "%PYTHON%" -c "import llama_cpp, gradio, sentence_transformers, rank_bm25, fitz, numpy, psutil, cryptography" >nul 2>nul
    IF ERRORLEVEL 1 (
        echo [AVISO] Algunos modulos no estan disponibles en el WinPython bundled.
        echo         Esto puede indicar que la USB no fue preparada correctamente.
        echo         Contacta al administrador del proyecto.
        echo.
    ) ELSE (
        echo [OK] Todos los paquetes verificados.
    )

    REM Marcar primera ejecucion como completada
    echo done > "%SETUP_FLAG%"
)

REM -- Verificar Visual C++ Redistributable ----------------------------------
where vcruntime140.dll >nul 2>nul
IF ERRORLEVEL 1 (
    IF EXIST "%BASE_DIR%engine\vcredist\vc_redist.x64.exe" (
        echo [INFO] Instalando Visual C++ Redistributable...
        "%BASE_DIR%engine\vcredist\vc_redist.x64.exe" /install /quiet /norestart
        echo [OK] Visual C++ Redistributable instalado.
    ) ELSE (
        echo [AVISO] Visual C++ Redistributable no encontrado.
        echo         Si el sistema falla, instala engine\vcredist\vc_redist.x64.exe
    )
)

REM -- Variables de entorno: modo 100%% OFFLINE ------------------------------
SET HF_HUB_OFFLINE=1
SET TRANSFORMERS_OFFLINE=1
SET HF_HOME=%BASE_DIR%models\.cache\huggingface
SET SENTENCE_TRANSFORMERS_HOME=%BASE_DIR%models\.cache\sentence_transformers
SET GRADIO_ANALYTICS_ENABLED=False
SET PYTHONPATH=%BASE_DIR%engine\python\Lib\site-packages;%BASE_DIR%app
SET PATH=%BASE_DIR%engine\python;%PATH%

REM -- Arrancar --------------------------------------------------------------
echo [OK] Iniciando Pocket Mentor EDU...
echo [OK] La interfaz abrira en: http://localhost:8000
echo [OK] Si no se abre automaticamente, ingresa a esa direccion en tu navegador.
echo [OK] El navegador se abrira en unos segundos...
echo [OK] Para detener el sistema, cierra esta ventana.
echo.

REM Lanzar el navegador despues de 4 segundos sin bloquear a Python
start /b cmd /c "ping -n 5 127.0.0.1 >nul & start http://localhost:8000"

"%PYTHON%" "%APP%"

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] El sistema se detuvo con errores.
    echo Revisa logs\system.log para mas detalles.
    pause
)
