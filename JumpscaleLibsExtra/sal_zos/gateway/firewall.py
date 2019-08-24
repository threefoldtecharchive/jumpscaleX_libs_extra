from .. import templates


class Firewall:
    def __init__(self, container, networks, forwards, routes):
        """

        """
        self.container = container
        self.networks = networks
        self.forwards = forwards
        self.routes = routes or []

    def apply_rules(self):
        # nftables
        publicnetworks = list(filter(lambda net: net.public, self.networks))
        privatenetworks = list(filter(lambda net: not net.public, self.networks))
        routed_devs = set(route.dev for route in self.routes)
        nftables = templates.render(
            "nftables.conf",
            publicnetwork=publicnetworks[0],
            privatenetworks=privatenetworks,
            routes=self.routes,
            routed_devs=routed_devs,
            portforwards=self.forwards,
        )
        self.container.upload_content("/etc/nftables.conf", nftables)
        job = self.container.client.system("nft -f /etc/nftables.conf").get()
        if job.state != "SUCCESS":
            raise j.exceptions.Base("Failed to apply nftables {} {}".format(job.stdout, job.stderr))
