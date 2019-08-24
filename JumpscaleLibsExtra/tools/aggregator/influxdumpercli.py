from Jumpscale import j

j.builders.bash.locale_check()
import click


@click.command()
@click.option("--influx-host", default="127.0.0.1", help="address of the influxdb server")
@click.option("--influx-port", default=8086, help="port of the http interface of influxdb server")
@click.option("--influx-login", default="root", help="login of influxdb server")
@click.option("--influx-pasword", help="password of influxdb server")
@click.option("--db", default="statistics", help="database name to use")
@click.option("--scan-cidr", default="127.0.0.1/24", help="cidr on which scan for redis server")
@click.option("--workers", default=4, help="Add amount of workers")
@click.option("--redis-port", default=[9999], multiple=True, help="listening redis port")
@click.option(
    "--rentention-duration", default="5d", help="default retention policy duration to set to the influxdb database used"
)
def influxdumper(
    influx_host, influx_port, influx_login, influx_pasword, db, scan_cidr, redis_port, rentention_duration, workers
):
    """
    InfluxDumper is a process that will scan the network specified by scan-dir for open ports specified by redis-port.
    The dumper will then read from the redis server found and dump the aggregated statistics into influxdb
    """
    influx_client = j.clients.influxdb.get(
        data={"host": influx_host, "port": influx_port, "username": influx_login, "database": db}
    )
    j.tools.realityprocess.influxpump(
        influx_client, cidr=scan_cidr, ports=redis_port, rentention_duration=rentention_duration, workers=workers
    )


if __name__ == "__main__":
    influxdumper()
