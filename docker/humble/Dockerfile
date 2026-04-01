FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-lc"]

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY docker/humble/apt-packages.txt /tmp/apt-packages.txt
RUN apt-get update \
    && xargs -a /tmp/apt-packages.txt apt-get install -y --no-install-recommends \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/* /tmp/apt-packages.txt

RUN rosdep init 2>/dev/null || true
RUN rosdep update || true

COPY docker/humble/entrypoint.sh /ros_entrypoint_local.sh
RUN chmod +x /ros_entrypoint_local.sh

WORKDIR /workspaces/multi-FTS
ENTRYPOINT ["/ros_entrypoint_local.sh"]
CMD ["bash"]
