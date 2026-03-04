#!/bin/bash


#!/bin/bash

# Get number of GPUs on the system
GPU_COUNT=$(nvidia-smi -L | wc -l)

# Build the docker run command with the appropriate number of GPUs
DOCKER_CMD=("docker" "run" "-d" "--rm" "--runtime=nvidia" "-e" "NVIDIA_VISIBLE_DEVICES=all")
    #"--device=/dev/nvidia-uvm"
    #"--device=/dev/nvidia-uvm-tools"
    #"--device=/dev/nvidia-modeset"
    #"--device=/dev/nvidiactl")

#for ((i=0; i<${GPU_COUNT}; i++)); do
#  DOCKER_CMD+=("--device=/dev/nvidia$i")
#done

DOCKER_CMD+=("nvcr.io/nvidia/cuda:12.0.0-base-ubuntu20.04" "bash" "-c" "while [ true ]; do nvidia-smi -L; sleep 5; done")

# Print the command for debugging
echo "${DOCKER_CMD[@]}"

# Run the docker command
CONTAINER_ID=$("${DOCKER_CMD[@]}")

echo "Started container with ID: ${CONTAINER_ID}"

# Give the container some time to start and run the command
sleep 10

# Trigger a systemd daemon reload
sudo systemctl daemon-reload

# Give the system some time to process the reload
sleep 10

docker logs ${CONTAINER_ID}

# Check the logs for the error message
ERROR_COUNT=$(docker logs ${CONTAINER_ID} | grep -c "Failed to initialize NVML: Unknown Error")

# If the error count is more than 0, the machine has the problem
if [[ ${ERROR_COUNT} -gt 0 ]]; then
  echo "The machine has the problem. NVML: Unknown Error"
else
  echo "The machine does not have the problem."
fi

# Clean up - stop the container
docker stop ${CONTAINER_ID}
