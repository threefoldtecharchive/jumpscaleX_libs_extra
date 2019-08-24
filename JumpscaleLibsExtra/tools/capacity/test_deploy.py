from Jumpscale import j

ZT_ID = "12ac4a1e716b16cc"
ZT_TOKEN = "8DaFJC9cyQBaQnHB6gsgwVKJsuRrUySG"
KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCtRRg+Hj3CB/1kPaWMExXFmUAIti6wirVrURsEvz/d0eJeQJok7Fy1npoAgtBEGn9LVrmL2jyefAZSggPkxtRLbUvWBDraZoJGRtzrEo9nf5z6YrCnGG+Od+HbP5aoHkq9ykEsyDcdTNInvW+qeClE0vtA4zuQ/QxcAV293yq+4HQRRoH1EosodONjsLDb8D20Z36Fmc6VTxtMC5yvvNal+si/XelKha7ri/Su/mCSV+IwnA2Ph5XZPe4JYUdD529CTdfjcwyN3CShtwNNFG72YYWwxKPHQFs/5QlwvbXUmLEjz7gF50qaeeGKibDRWOkxjV8wnBUXKShC5waZCRTd zaibon@zaibon.be"
NODES = ["local"]


def main():
    # create VMs
    for i, instance in enumerate(NODES[:2]):
        robot = j.clients.zrobot.robots[instance]

        self._log_info("create zerotier client used to authorize VM to the network")
        zt_client_instance = "ztclient"
        zt = robot.services.find_or_create("zerotier_client", zt_client_instance, {"token": ZT_TOKEN})

        self._log_info("create vdisk")
        vdiskargs = {"disktype": "HDD", "size": 5, "filesystem": "btrfs", "mountpoint": "/mnt/data"}
        vdisk = robot.services.find_or_create("vdisk", "capacity_registration_datadisk", vdiskargs)
        vdisk.schedule_action("install").wait(die=True)

        # nsargs = {'disktype': 'HDD', 'mode': 'user', 'size': 40}
        # ns = robot.services.find_or_create('namespace', 'capacity_registration_datadisk', nsargs)
        # ns.schedule_action('install').wait(die=True)

        disk_url = vdisk.schedule_action("private_url").wait(die=True).result

        self._log_info("create vm")
        vmargs = {
            "memory": 256,
            "cpu": 1,
            "nics": [
                {"type": "default", "name": "nat0"},
                {"type": "zerotier", "id": ZT_ID, "name": "zt0", "ztClient": zt_client_instance},
            ],
            "flist": "https://hub.grid.tf/gig-bootable/ubuntu:lts.flist",
            "disks": [{"url": disk_url, "name": "data1", "mountPoint": "/mnt", "filesystem": "btrfs"}],
            "configs": [{"name": "sshkey", "path": "/root/.ssh/authorized_keys", "content": KEY_PUB}],
        }
        vm = robot.services.find_or_create("vm", "capacity_registration_vm%d" % i, vmargs)
        vm.schedule_action("install").wait(die=True)
        vm.schedule_action("enable_vnc")


#     # robot = j.clients.zrobot.robots[NODES[3]]
#     # data = {
#     #     # TODO
#     # }
#     # gateway = robot.services.create('gateway', 'gw_etcd', data)
#     # gateway.schedule_action('install').wait()


if __name__ == "__main__":
    main()
