import logging
import sys
import asyncio
from azure.devops.v5_1.task_agent.task_agent_client import TaskAgentClient
from aps.config import get_pool_configs
from aps.devops import DevOpsConnection
from aps.pool_management import manage_pool


logging.basicConfig(level=logging.INFO)
connection = DevOpsConnection()

loop = asyncio.get_event_loop()


for config in get_pool_configs():
    res = connection.get_agent_pools(pool_name=config.pool)
    if len(res) != 1:
        logging.error(f'Could not find agent pool with name {config.pool}')
        sys.exit(-1)

    logging.info(f'Starting task to manage agent pool {config.pool}')
    config.pool_id = res[0].id
    loop.create_task(manage_pool(connection, config))

loop.run_forever()
