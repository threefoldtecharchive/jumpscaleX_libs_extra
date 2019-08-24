from Jumpscale import j

j.builders.bash.locale_check()
import click
from tools.aggregator.Dumper import BaseDumper


class DumperTest(BaseDumper):
    def dump(self, redis):
        """
        Dump, gets a redis connection. It must process the queues of redis until there is no more items to
        process and then immediately return.

        :param redis: redis connection
        :return:
        """
        """
        :param redis:
        :return:
        """
        print("Dumping for client {}".format(redis))
        redis.ping()
        return True


@click.command()
@click.option("--scan-cidr", default="127.0.0.1/24", help="cidr on which scan for redis server")
@click.option("--workers", default=4, help="Add amount of workers")
@click.option("--redis-port", default=[9999], multiple=True, help="listening redis port")
@click.option("--scan-interval", default=30, type=int, help="Scan interval")
def tester(scan_cidr, redis_port, workers, scan_interval):
    """
    Test Dumper
    """
    dumper = DumperTest(scan_cidr, redis_port, scan_interval)
    dumper.start(workers)


if __name__ == "__main__":
    tester()
