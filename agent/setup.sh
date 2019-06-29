#!/bin/bash

rm -rf /azp/agent
mkdir /azp/agent
cd /azp/agent

curl -LsS $AGENT_URL | tar -xz & wait $!
