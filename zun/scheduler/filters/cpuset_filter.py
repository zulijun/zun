# Copyright (c) 2017 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging

from zun.scheduler import filters

LOG = logging.getLogger(__name__)


class CPUSETFilter(filters.BaseHostFilter):
    """Filter the host by cpu and memory request of cpuset"""

    run_filter_once_per_request = True

    def host_passes(self, host_state, container, extra_spec):
        mem_available = host_state.mem_free - host_state.mem_used
        pinned_cpus_flag = False
        for numa_node in host_state.numa_topology.nodes:
            if numa_node.pinned_cpus:
                pinned_cpus_flag = True

        if container.cpu_policy == 'dedicated':
            if host_state.total_containers and (not pinned_cpus_flag):
                return False
            else:
                for numa_node in host_state.numa_topology.nodes:
                    if len(numa_node.cpuset) - len(
                            numa_node.pinned_cpus) > container.cpu and numa_node.mem_available > int(
                        container.memory[:-1]):
                        host_state.limits['cpuset'] = {'node': numa_node.id, 'cpuset_cpu': numa_node.cpuset,
                                                      'cpuset_mem': numa_node.mem_available}
                        return True
                    else:
                        return False
        else:
            container.cpu_policy = 'shared'
            if not pinned_cpus_flag:
                if container.memory:
                    if mem_available >= container.memory:
                        return True
                    else:
                        return False
                else:
                    return True
            else:
                return False
