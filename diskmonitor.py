import shutil
import subprocess
import logging
import sys

# Configure logging to track automation behavior
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

THRESHOLD_PERCENT = 90.0
TARGET_PATH = "/"

def check_and_clean_disk():
    try:
        # 1. Fetch disk metrics safely using built-in shutil
        total, used, free = shutil.disk_usage(TARGET_PATH)
        used_percent = (used / total) * 100
        logging.info(f"Current disk usage on {TARGET_PATH}: {used_percent:.2f}%")

        # 2. Evaluate against alert threshold
        if used_percent > THRESHOLD_PERCENT:
            logging.warning(f"Disk usage exceeded {THRESHOLD_PERCENT}%. Initiating safe cleanup...")
            
            # 3. Execute a safe, non-destructive system cleanup command
            # Using subprocess.run with check=True to catch errors if the command fails
            result = subprocess.run(
                ["docker", "system", "prune", "-f"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            logging.info("Cleanup successful. Command output:")
            logging.info(result.stdout)
        else:
            logging.info("Disk space is within safe operational limits.")

    except shutil.Error as se:
        logging.error(f"Filesystem path error: {se}")
        sys.exit(1)
    except subprocess.CalledProcessError as cpe:
        logging.error(f"Cleanup command failed with exit code {cpe.returncode}: {cpe.stderr}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected automation failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_and_clean_disk()
