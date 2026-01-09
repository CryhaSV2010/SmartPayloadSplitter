@echo off
echo Running Smart Payload Splitter Client...
echo.
echo Example: Sending test payload to local server
echo.
python client/payload_fragmenter.py test_payload.txt -u http://localhost:5000 --assemble
pause
