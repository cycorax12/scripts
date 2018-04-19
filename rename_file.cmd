@ECHO OFF

SETLOCAL ENABLEDELAYEDEXPANSION

REM ren "C:\Virendra\batch scripts\2009101_67070_deal ticket(apple)_2009120000005.csv" "2009101_67070_dealticket_2009120000005.csv"
REM ren "C:\Virendra\batch scripts\2009101_67070_deal ticket(apple)_2009120000005.csv" "2009101_67070_dealticket_2009120000005.csv"

REM below commmand loops over each  file in given directory, filters *.csv file and renames
for %%a in (C:\Virendra\batch-scripts\*.csv) do  (
	REM ren "%%a" "%finalName%"
	set test=
	call :RenameFile "%%a" test
	echo %%a 
	echo !test!
	ren "%%a" "!test!"
	pause
)

goto:End



:RenameFile
    set fileName=%1
	set actualFile=%1
	echo Actual File %actualFile%
	
	call :getlasttoken %fileName%
	
	set fileName=%lasttoken%
	echo %fileName%
	
		
	pause
	REM SET "fileName=20090101_67070_deal tic	ket(apple)_2009120000005.csv"
	for /f "tokens=1 delims=()" %%i in ("%fileName%") do (set prefix=%%i)
	ECHO We're working with "%fileName%"
	set fileName=%fileName: =%
	ECHO Removing space to get "%fileName%"
	pause
	
	for /f "tokens=1 delims=()" %%i in ("%fileName%") do (set prefix=%%i)
	ECHO prefix is "%prefix%"
	for /f "tokens=4 delims=_" %%i in ("%fileName%") do (set suffix=%%i)
	ECHO suffix is "%suffix%"
	set finalName=%prefix%_%suffix%
	echo FinalName "%finalName%"
	set %2=%finalName%
	REM ren %1% "%finalName%"
:END 



:getlasttoken
set "check=%~1"
:loop
if defined check (
for /f "delims=\ tokens=1*" %%x in ("%check%") do (
set "lasttoken=%%x"
set "check=%%y"
)
goto loop
) else exit/b
