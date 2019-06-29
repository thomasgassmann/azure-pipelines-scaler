import yaml
from typing import List
from msrest.authentication import BasicAuthentication
from azure.devops.connection import Connection

with open('config.yml') as handle:
    config = yaml.safe_load(handle)


class DevOpsCredentials:
    def __init__(self, url, pat):
        self.url = url
        self.pat = pat


class PoolConfig:
    def __init__(self, pool, image, target_worker_count):
        self.pool = pool
        self.image = image
        self.target_worker_count = target_worker_count
        self.pool_id = None


def get_azure_devops_credentials() -> DevOpsCredentials:
    devops_config = config['azure_devops']
    return DevOpsCredentials(devops_config['url'], devops_config['pat'])


def get_azure_devops_connection() -> Connection:
    credentials = get_azure_devops_credentials()
    return Connection(base_url=credentials.url, creds=BasicAuthentication('', credentials.pat))


def get_agent_dockerfile() -> str:
    return config['config']['agent_dockerfile']


def get_poll_interval() -> int:
    return config['config']['poll_interval']


def get_pool_configs() -> List[PoolConfig]:
    pools = config['config']['pools']
    for pool in pools:
        yield PoolConfig(pool['pool'], pool['image'], pool['target_worker_count'])
