import io

import requests

from Jumpscale import j


class Capacity:
    def __init__(self, node):
        self._node = node

    def total_report(self):
        """
        create a report of the total hardware capacity for
        processor, memory, motherboard and disks
        """
        cl = self._node.client
        n = self._node

        return j.tools.capacity.parser.get_report(cl.info.cpu(), cl.info.mem(), n.disks.list())

    def reality_report(self):
        """
        create a report of the actual used hardware capacity for
        processor, memory, motherboard and disks
        """
        total_report = self.total_report()

        return j.tools.capacity.reality_parser.get_report(
            disks=self._node.disks.list(),
            storage_pools=self._node.storagepools.list(),
            total_cpu_nr=total_report.CRU,
            used_cpu=self._node.client.aggregator.query("machine.CPU.percent"),
            used_memory=self._node.client.info.mem()["used"],
        )

    def node_parameters(self):
        params = []
        checking = ["development", "debug", "support"]

        for check in checking:
            if self._node.kernel_args.get(check) is not None:
                params.append(check)

        return params

    def directory(self):
        if "staging" in self._node.kernel_args:
            # return a staging directory object
            data = {"base_uri": "https://staging.capacity.threefoldtoken.com"}
            return j.clients.threefold_directory.get("staging", data=data, interactive=False)

        # return production directory
        return j.clients.threefold_directory.get(interactive=False)

    def register(self):
        farmer_id = self._node.kernel_args.get("farmer_id")
        if not farmer_id:
            return False

        # checking kernel parameters enabled
        parameters = self.node_parameters()

        robot_address = ""
        public_addr = self._node.public_addr
        if public_addr:
            robot_address = "http://%s:6600" % public_addr
        os_version = "{branch} {revision}".format(**self._node.client.info.version())

        report = self.total_report()
        data = dict(
            node_id=self._node.node_id,
            location=report.location,
            total_resources=report.total(),
            robot_address=robot_address,
            os_version=os_version,
            parameters=parameters,
            uptime=int(self._node.uptime()),
        )
        data["farmer_id"] = farmer_id

        if "private" in self._node.kernel_args:
            data["robot_address"] = "private"
        elif not data["robot_address"]:
            raise j.exceptions.Base("Can not register a node without robot_address")

        client = self.directory()

        try:
            _, resp = client.api.RegisterCapacity(data)
        except requests.exceptions.HTTPError as err:
            j.tools.logger._log_error("error pusing total capacity to the directory: %s" % err.response.content)

    def update_reality(self):
        farmer_id = self._node.kernel_args.get("farmer_id")
        if not farmer_id:
            return False

        report = self.reality_report()
        data = dict(
            node_id=self._node.node_id,
            farmer_id=farmer_id,
            cru=report.CRU,
            mru=report.MRU,
            hru=report.HRU,
            sru=report.SRU,
        )

        client = self.directory()

        resp = client.api.UpdateActualUsedCapacity(data=data, node_id=self._node.node_id)
        resp.raise_for_status()

    def update_reserved(self, vms, vdisks, gateways):
        farmer_id = self._node.kernel_args.get("farmer_id")
        if not farmer_id:
            return False

        report = j.tools.capacity.reservation_parser.get_report(vms, vdisks, gateways)
        data = dict(
            node_id=self._node.node_id,
            farmer_id=farmer_id,
            cru=report.CRU,
            mru=report.MRU,
            hru=report.HRU,
            sru=report.SRU,
        )

        client = self.directory()

        resp = client.api.UpdateReservedCapacity(data=data, node_id=self._node.node_id)
        resp.raise_for_status()
