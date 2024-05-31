import schedule
import time
import subprocess

def run_spider(spider_name):
    result = subprocess.run(['scrapy', 'crawl', spider_name], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Spider {spider_name} completed successfully")
    else:
        print(f"Spider {spider_name} failed with error: {result.stderr}")

def schedule_task():
    schedule.every().monday.at("15:00").do(run_spider, "funds")
    schedule.every().monday.at("15:00").do(run_spider, "grants")
    schedule.every().monday.at("15:00").do(run_spider, "eureka")

if __name__ == "__main__":
    schedule_task()
    while True:
        schedule.run_pending()
        time.sleep(1)
