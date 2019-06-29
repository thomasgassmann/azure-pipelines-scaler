import requests
import base64
import json
import logging
from typing import List
from azure.devops.v5_1.task_agent.models import TaskAgent, TaskAgentPool
from azure.devops.v5_1.task_agent.task_agent_client import TaskAgentClient
from aps.config import get_azure_devops_connection, get_pool_configs, PoolConfig


class Agent:
    def __init__(self, id, name, status):
        self.name = name
        self.id = id
        self.status = status


class JobRequest:
    def __init__(self, request_id, result, plan_type, reserved_agent_id, reserved_agent_name, reserved_agent_status):
        self.request_id = request_id
        self.result = result
        self.plan_type = plan_type
        self.reserved_agent = Agent(
            reserved_agent_id, reserved_agent_name, reserved_agent_status)
        self.running = plan_type == 'Build' and result is None


class DevOpsConnection:

    def __init__(self):
        self._connection = get_azure_devops_connection()
        self._connection.authenticate()

        self._task_agent_client: TaskAgentClient = self._connection.clients_v5_1.get_task_agent_client()

    def get_agents(self, pool_id) -> List[TaskAgent]:
        return self._task_agent_client.get_agents(pool_id)

    def get_agent_pools(self, pool_name) -> List[TaskAgentPool]:
        return self._task_agent_client.get_agent_pools(pool_name=pool_name)

    def remove_agent(self, pool_id, agent_id):
        self._task_agent_client.delete_agent(pool_id, agent_id)

    def get_job_requests(self, pool_id) -> List[JobRequest]:
        # not yet included in API client, execute request manually
        # already implemented in ts client https://github.com/microsoft/azure-devops-extension-api
        url = self._connection.base_url + \
            f'/_apis/distributedtask/pools/{pool_id}/jobrequests'
        auth_token = base64.b64encode(
            (':' + self._connection._creds.password).encode('utf-8'))
        resp = requests.get(url, headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': b'Basic ' + auth_token
        })
        if resp.status_code != 200:
            raise ConnectionError()

        obj = json.loads(resp.content)
        ls = []
        for val in obj['value']:
            request_id = val['requestId']
            if 'reservedAgent' not in val:
                logging.warn(f'Skipping job, no reserved agent: {request_id}')
                continue
            reserved_agent = val['reservedAgent']
            ls.append(JobRequest(request_id,
                                 val['result'] if 'result' in val else None,
                                 val['planType'],
                                 reserved_agent['id'],
                                 reserved_agent['name'],
                                 reserved_agent['status']))
        return ls
