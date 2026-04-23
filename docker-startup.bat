@echo off
REM Docker Startup Script for IntelliGrocery PostgreSQL + pgAdmin4
REM Usage: docker-startup.bat [start|stop|restart|clean|status|logs]

setlocal enabledelayedexpansion

if "%1"=="" (
    set ACTION=start
) else (
    set ACTION=%1
)

if "%ACTION%"=="start" (
    echo [*] Starting IntelliGrocery services...
    docker-compose up -d
    timeout /t 5 /nobreak
    
    echo.
    echo [+] Services started!
    echo.
    echo Access Points:
    echo    - PostgreSQL:  localhost:5432
    echo    - pgAdmin4:    http://localhost:5050
    echo    - Streamlit:   http://localhost:8501
    echo.
    echo Credentials:
    echo    - PostgreSQL User: intelligrocery, Pass: IntelliGrocery@2024
    echo    - pgAdmin4 Email: admin@intelligrocery.local, Pass: AdminPass@2024
    echo.
    echo Next step:
    echo    streamlit run frontend/app.py
    
) else if "%ACTION%"=="stop" (
    echo [*] Stopping IntelliGrocery services...
    docker-compose down
    echo [+] Services stopped!
    
) else if "%ACTION%"=="restart" (
    echo [*] Restarting IntelliGrocery services...
    docker-compose down
    timeout /t 2 /nobreak
    docker-compose up -d
    timeout /t 5 /nobreak
    echo [+] Services restarted!
    
) else if "%ACTION%"=="clean" (
    echo [!] WARNING: This will delete all data!
    set /p confirm="Continue? (y/n): "
    if /i "!confirm!"=="y" (
        echo [*] Cleaning up...
        docker-compose down -v
        echo [+] Cleanup complete!
    ) else (
        echo Cancelled.
    )
    
) else if "%ACTION%"=="status" (
    echo [*] Container Status:
    docker-compose ps
    echo.
    echo [*] Database Info:
    docker exec intelligrocery_db psql -U intelligrocery -d intelligrocery -c "\l"
    
) else if "%ACTION%"=="logs" (
    if "%2"=="" (
        docker-compose logs -f
    ) else (
        docker-compose logs -f %2
    )
    
) else (
    echo Usage: docker-startup.bat [start^|stop^|restart^|clean^|status^|logs]
    echo.
    echo Commands:
    echo   start    - Start all services
    echo   stop     - Stop all services
    echo   restart  - Restart all services
    echo   clean    - Delete all data [!]
    echo   status   - Show container status
    echo   logs     - Show service logs
    echo.
    echo Examples:
    echo   docker-startup.bat start
    echo   docker-startup.bat logs postgres
    exit /b 1
)

endlocal
