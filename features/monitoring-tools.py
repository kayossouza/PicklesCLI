import os
import psutil

def monitor_system():
    # CPU Usage
    cpu_usage = psutil.cpu_percent()
    # RAM Usage
    mem_usage = psutil.virtual_memory().percent
    # Disk Usage
    disk_usage = psutil.disk_usage('/').percent

    print(f'CPU Usage: {cpu_usage}%')
    print(f'Memory Usage: {mem_usage}%')
    print(f'Disk Usage: {disk_usage}%')

if __name__ == '__main__':
    monitor_system()
