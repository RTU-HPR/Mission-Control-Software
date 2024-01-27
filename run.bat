@echo off
start cmd /k "cd Processing && python main.py"

start cmd /k "cd Yamcs && mvnw yamcs:run"

start cmd /k "cd OpenMct && npm start"