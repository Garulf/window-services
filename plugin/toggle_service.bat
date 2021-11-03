@echo on
setlocal

SET STATE=%1%
SET SERVICE=%2%

net %STATE% %SERVICE%

endlocal