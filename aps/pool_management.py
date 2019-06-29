import asyncio
import uuid
import logging
import sympy
from collections.abc import Iterable
from aps.devops import DevOpsConnection
from aps.config import PoolConfig, get_agent_dockerfile, get_poll_interval
from aps.dockerfiles import build_worker_image, start_container, get_worker_name, stop_container


def evaluate_target_worker_count(expr: str, var_dict: dict):
    key_list = sorted([key for key in var_dict])
    created_syms = sympy.symbols(' '.join(key_list))
    target_dict = dict()
    if isinstance(created_syms, Iterable):
        for i in range(len(key_list)):
            target_dict[created_syms[i]] = var_dict[key_list[i]]
    else:
        target_dict[created_syms] = var_dict[key_list[0]]
    return int(sympy.sympify(expr).evalf(subs=target_dict))


async def manage_pool(connection: DevOpsConnection, config: PoolConfig):
    image_name = build_worker_image(config.image, get_agent_dockerfile())
    poll_interval = get_poll_interval()
    while True:
        await asyncio.sleep(poll_interval)

        agents = [agent for agent in connection.get_agents(
            config.pool_id) if agent.enabled and agent.status == 'online']
        jobs = connection.get_job_requests(config.pool_id)
        target_workers = evaluate_target_worker_count(config.target_worker_count, {
            'JOB_COUNT': len([req for req in jobs if req.running]),
            'AGENT_COUNT': len(agents)
        })

        if len(agents) == target_workers:
            logging.info('Nothing to do...')
            continue

        difference = len(agents) - target_workers
        logging.info(
            f'Difference in worker count for pool {config.pool}: {str(-difference)}')
        if difference < 0:
            logging.info(
                f'Adding {str(-difference)} workers to pool {config.pool}...')
            for _ in range(-difference):
                worker_name = get_next_worker_name(agents, config.image)
                container = start_container(image_name, config, worker_name)
                logging.info(f'Started container for pool {config.pool}')
        else:
            logging.info(f'Removing {str(-difference)} agents form queue...')
            agents_to_kill = sorted(
                get_free_agents(agents, jobs))[-difference:]
            logging.info(f'Found {len(agents_to_kill)} with no job to kill...')
            for agent_name in agents_to_kill:
                logging.info(f'Removing agent {agent_name}...')
                stop_container(agent_name, image_name)
                corresponding_agent = list([
                    agent for agent in agents if agent.name == agent_name])[0]
                connection.remove_agent(config.pool_id, corresponding_agent.id)
                logging.info(
                    f'Successfully removed {agent_name} from pool {config.pool}')


def get_free_agents(active_agents, jobs):
    running_jobs = [job for job in jobs if job.running]
    reserved_agent_names = [job.reserved_agent.name for job in running_jobs]
    return [agent.name for agent in active_agents if agent.name not in reserved_agent_names]


def get_next_worker_name(agents, image):
    names = [agent.name for agent in agents]
    index = 0
    agent_name = get_worker_name(image, worker_id=index)
    while agent_name in names:
        agent_name = get_worker_name(image, worker_id=index)
        index += 1
    return agent_name
