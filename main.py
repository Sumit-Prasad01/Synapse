import subprocess
import threading
import time
from dotenv import load_dotenv

from app.utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()


def run_backend():
    try:

        logger.info("Starting backend service.")
        subprocess.run(["python", "app/api.py"], check = True)

    except Exception as e:
        logger.error("Problem with backend service")
    

def run_frontend():
    try:

        logger.info("Starting frontend service")
        subprocess.run(["streamlit", "run", "streamlit_app.py"], check = True)
    
    except Exception as e:
        logger.error("Problem with frontend service")
        

if __name__ == "__main__":
    try:

        threading.Thread(target = run_backend).start()
        time.sleep(2)
        run_frontend()

    except Exception as e:
        logger.exception(f"Custom Exception occured : {str(e)}")