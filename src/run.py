import sys
sys.path.append("..")
from setting import *
from producer_sextant import run_schedule
import subprocess
import time

if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))

    commandRunConsumer = 'python3 consumer.py'
    processRunConsumer = subprocess.Popen(commandRunConsumer, shell=True, cwd=current_directory)
    print('Consumer is running...')

    time.sleep(10)

    commandRunFlower = 'celery --broker={broker} flower'.format(
        broker=BROKER_URL
    )
    processRunFlower = subprocess.Popen(commandRunFlower, shell=True, cwd=current_directory)
    print('Flower is running...')

    time.sleep(10)

    print('Start event loop schedule......')
    run_schedule()
