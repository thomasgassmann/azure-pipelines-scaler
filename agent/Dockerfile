ARG POOL_IMAGE=python

FROM $POOL_IMAGE
# replace pool docker file and setup agent
ARG AGENT_URL=https://vstsagentpackage.azureedge.net/agent/2.153.2/vsts-agent-linux-x64-2.153.2.tar.gz

ENV AZP_URL=${AZP_URL}
ENV AGENT_URL=${AGENT_URL}

# TODO: fix for other distros
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    jq \
    git \
    iputils-ping \
    libcurl3

WORKDIR /azp

COPY ./setup.sh .
RUN chmod +x setup.sh && bash /azp/setup.sh

COPY ./start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]
