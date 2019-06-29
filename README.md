# Azure Pipelines Scaler
> Autoscale your Azure Pipelines Build Agents horizontally as needed

## Getting started
Azure Pipelines Scaler (`aps`) uses a YAML file to specify which build queues on Azure Pipelines it should manage. 
```yaml
config:
  agent_dockerfile: ./agent
  poll_interval: 20
  pools:
    - pool: example
      image: ./config/definitions/example
      target_worker_count: "JOB_COUNT + 1"
azure_devops:
  pat: secret_here
  url: https://dev.azure.com/thomasgassmann
```
In the above example config the pool with the name `example` will be autoscaled. For each pool managed by `aps` an `image` and a `target_worker_count` have to be specified.

The `image` property is a path to a folder with a `Dockerfile`. This `Dockerfile` should contain the definition of how the build agent is going to look.

*Important to notice is, that all images should have a debian base-image (`apt-get` is required).*

`aps` will then build another image based on the image specified in `image`, add the build agent and start autoscaling the queue.

The `target_worker_count` property determines how many build agents the queue should have. This property supports maths expressions with predefined variables. Currently there are two predefined variables (`JOB_COUNT` and `AGENT_COUNT`). In the example above `aps` would autoscale the agent pool `example` to always have at least one more build agents than there are jobs in the queue.

Additionally a PAT (personal access token) and the URL to your Azrue DevOps tenant have to be specified. The PAT needs to have access to build queues and builds in order to autoscale.


```docker
docker run
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /path/config:/app/config \
    thomasgassmann/aps:latest
```
