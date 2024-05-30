from prefect import task, Flow
from prefect.storage import GitHub
from prefect.run_configs import UniversalRun
import subprocess

@task
def run_spider(spider_name):
    subprocess.run(['scrapy', 'crawl', spider_name], check=True)

with Flow("scrapy_flow") as flow:
    grants = run_spider("grants")
    gunds = run_spider("gunds")
    eureka = run_spider("eureka")

    grants.set_downstream(gunds)
    gunds.set_downstream(eureka)

flow.storage = GitHub(repo="Amaani5668/PERFECT", path="https://github.com/Amaani5668/PERFECT.git")
flow.run_config = UniversalRun()

flow.register(project_name="my-scrapy-project")
