# Description: This script is used to run the Processing application using the virtual environment.

# Activate the virtual environment
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Recovery_Processing ; .\env\Scripts\Activate.ps1 ;"
# Install requirements
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Recovery_Processing ; pip install -r requirements.txt ;"
# Start the Processing application
Start-Process -FilePath "powershell" -ArgumentList "-Command cd Recovery_Processing ; python main.py ;"
