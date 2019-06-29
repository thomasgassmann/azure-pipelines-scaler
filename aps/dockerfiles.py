import docker
import logging
import os
import asyncio
from docker.models.containers import Container
from aps.config import PoolConfig, get_azure_devops_credentials

client = docker.from_env()


def start_container(name: str, config: PoolConfig, worker_id: str) -> Container:
    credentials = get_azure_devops_credentials()
    env = {
        'AZP_URL': credentials.url,
        'AZP_PAT': credentials.pat,
        'AZP_AGENT_NAME': worker_id,
        'AZP_POOL': config.pool
    }
    return client.containers.run(name, environment=env, detach=True,
                                 volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}})


def stop_container(name: str, image_name: str):
    containers = client.containers.list(
        filters={'status': 'running'})
    with_image = [
        container for container in containers if any([tag for tag in container.image.tags if image_name in tag])]

    base = 'unix://var/run/docker.sock' if os.name == 'posix' else 'npipe:////./pipe/docker_engine'
    api = docker.APIClient(base_url=base)
    selected = None
    for container in with_image:
        env_vars = api.inspect_container(container.id)['Config']['Env']
        key = f'AZP_AGENT_NAME={name}'
        if key in env_vars:
            selected = container
            break

    if selected is None:
        raise ValueError()

    selected.stop()


def get_worker_name(dockerfile: str, worker_id: str = None) -> str:
    APS_PREFIX = 'aps_'
    name = APS_PREFIX + os.path.basename(dockerfile) + '_agent'
    if worker_id is not None:
        name += f'_{worker_id}'
    return name


def build_worker_image(dockerfile: str, agent_dockerfile: str) -> str:
    logging.info(f'Building worker image from dockerfile {dockerfile}...')
    name = get_worker_name(dockerfile)

    base_image_name = name + '_base'
    client.images.build(path=dockerfile, tag=base_image_name)

    build_args = {
        'POOL_IMAGE': base_image_name
    }
    client.images.build(path=agent_dockerfile,
                        tag=name,
                        buildargs=build_args)

    logging.info(f'Successfully built image {name}')

    return name
