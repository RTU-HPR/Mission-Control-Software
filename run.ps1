# This script starts the Processing, Yamcs and OpenMct applications in separate windows.
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Processing ; python main.py ;"
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Yamcs ; ./mvnw yamcs:run ;"
Start-Process -FilePath "powershell" -ArgumentList "-Command cd OpenMct ; npm start ;"