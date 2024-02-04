# Description: This script is used to start all the applications required for the mission control software. It starts the Processing application, Yamcs and OpenMct. It also opens the OpenMct and Yamcs applications in the default web browser.

# Activate the virtual environment, install requirements and start the Processing application
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Processing ; .\env\Scripts\Activate.ps1 ;"
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Processing ; pip install -r requirements.txt ;"
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Processing ; python main.py ;"
# Start the Yamcs and OpenMct applications
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Yamcs ; ./mvnw yamcs:run ;"
Start-Process -FilePath "powershell" -ArgumentList "-Command cd OpenMct ; npm start ;"

# Open localhost:9000 and localhost:8090
Start-Process -FilePath "http://localhost:8090"
Start-Process -FilePath "http://localhost:9000"

