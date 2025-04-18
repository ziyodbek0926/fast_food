import subprocess
import sys
import os
from threading import Thread
import time

def run_django():
    print("Starting Django server...")
    subprocess.run([sys.executable, "manage.py", "runserver"])

def run_bot():
    print("Starting Telegram bot...")
    subprocess.run([sys.executable, "run_bot.py"])

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("Error: .env file not found!")
        print("Please create a .env file with the following variables:")
        print("BOT_TOKEN=your_telegram_bot_token")
        print("ADMIN_USERNAME=admin")
        print("ADMIN_PASSWORD=admin123")
        sys.exit(1)

    # Run migrations
    print("Running migrations...")
    subprocess.run([sys.executable, "manage.py", "migrate"])

    # Initialize database
    print("Initializing database...")
    subprocess.run([sys.executable, "init_db.py"])

    # Start Django server in a separate thread
    django_thread = Thread(target=run_django)
    django_thread.daemon = True
    django_thread.start()

    # Wait for Django server to start
    time.sleep(2)

    # Start Telegram bot
    run_bot() 