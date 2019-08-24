import gevent
from Jumpscale import j


class Farm:
    def __init__(self, farmer_iyo_org):
        self.farmer_iy_org = farmer_iyo_org

    def list_nodes(self):
        capacity = j.clients.threefold_directory.get(interactive=False)
        resp = capacity.api.ListCapacity(query_params={"farmer": self.farmer_iy_org})[1]
        resp.raise_for_status()
        nodes = resp.json()

        def f(node):
            for key in ["total_resources", "used_resources", "robot_address"]:
                if key not in node:
                    return False
            return True

        return list(filter(f, nodes))

    def filter_online_nodes(self):
        def url_ping(node):
            try:
                j.sal.nettools.checkUrlReachable(node["robot_address"], timeout=5)
                return (node, True)
            except:
                return (node, False)

        group = gevent.pool.Group()
        for node, ok in group.imap_unordered(url_ping, self.list_nodes()):
            if ok:
                yield node
