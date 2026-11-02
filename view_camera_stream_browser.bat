@echo off
title Drishti - Edge Impulse Live Camera Stream
cls
echo =================================================================
echo  DRISHTI: LIVE GROVE VISION AI CAMERA STREAM (BROWSER)
echo  Runs 8-Class Model on Hardware and Opens Live Web Camera Feed
echo =================================================================
echo.
echo Connecting to Grove Vision AI Module V2...
echo Once started, open http://localhost:4912 in your browser to see
echo live camera frames with 8-class bounding boxes!
echo.
edge-impulse-run-impulse --continuous
echo.
pause
