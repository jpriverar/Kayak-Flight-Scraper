from datetime import datetime

class Logger:
    def __init__(self, path='.'):
        # Creating the log file where everything will be documented
        time = datetime.now()
        file_name = f"{path}/FlightFinder_" + time.strftime("%d-%m-%Y_%H-%M-%S") + ".log"
        self.log_file = open(file_name, 'w')

        # Writing important headers to the log file
        self.log_file.write(f'Execution started on {time.strftime("%d/%m/%Y at %H:%M:%S")}\n\n')

    def log(self, data):
        time = datetime.now()
        self.log_file.write(f'{time.strftime("%H:%M:%S")} > ')
        self.log_file.write(data + '\n')
        print(data)
