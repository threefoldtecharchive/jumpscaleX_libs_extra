from Jumpscale import j
from .InfluxDumper import InfluxDumper
import time
import random
import io
from Jumpscale import j

JSBASE = j.baseclasses.object


class AggregatorClientTest(j.baseclasses.object):
    TEST_INFLUX_DB = "test"

    def __init__(self):
        JSBASE.__init__(self)

    def _buildReport(self, actuals, reported):
        buffer = io.StringIO()
        errors = list()
        total_rate = 0
        reported_values = list()
        for i, point in enumerate(reported):
            actual = actuals[i]
            total_rate += actual["rate"]
            t = time.strptime(point["time"], "%Y-%m-%dT%H:%M:%SZ")
            reported_values.append("%s: %g" % (time.ctime(time.mktime(t)), point["value"]))
            if actual["avg"] != point["value"]:
                errors.append(
                    "[%s] Expected value: %g got %g" % (time.ctime(actual["stamp"]), actual["avg"], point["value"])
                )

        buffer.write("#" * 20 + "\n")
        buffer.write("Minutes: %d\n" % len(actuals))
        buffer.write("Avg Sample Rate: %d\n" % (total_rate / len(actuals)))
        buffer.write("Test result: %s\n" % ("ERROR" if errors else "OK"))
        buffer.write("#" * 20 + "\n")
        buffer.write("Expected values:\n")
        for actual in actuals:
            buffer.write("%s: %g\n" % (time.ctime(actual["stamp"]), actual["avg"]))

        buffer.write("Reported values:\n")
        for report in reported_values:
            buffer.write(report + "\n")

        buffer.write("ERRORS:\n")
        for err in errors:
            buffer.write(err)
            buffer.write("\n")
        else:
            buffer.write("No Errors\n")

        return buffer.getvalue()

    def statstest(self, aggregator, influxdb, points=100000, minutes=5):
        """
        Stats test will try to flood the redis instance with statistics data. and then generate a report with
        how many reports it did per second, and a sheet with the expected averages and times

        :note: The stats test will do a redis.flushall and flushdb before executing the test to make
             sure no garbage is accumulating from last test.

        :param aggregator: The aggregator client
        :param influxdb: Influx db client to validate values and generate reports
        :param points: How many points to report per minute
        :param minutes: Simulate reporting over
        :return:
        """

        # 1- Make sure to clean all the data stores (redis and influx) to avoid noise from previous tests.
        aggregator.redis.flushall()
        aggregator.redis.flushdb()
        for db in influxdb.get_list_database():
            if db["name"] == self.TEST_INFLUX_DB:
                influxdb.drop_database(self.TEST_INFLUX_DB)
        influxdb.create_database(self.TEST_INFLUX_DB)

        # 2- round the now to the nearist minute
        now = (int(time.time()) / 60) * 60

        # 3- push the start time to the future to make sure we avoid garbage from previous
        # tests
        now += 60
        random.seed(now)
        actuals = list()

        key = "test.key"
        stamp = 0
        # 4- Generate random test points.
        for minute in range(minutes):
            stamp = now + minute * 60
            lower = random.randint(0, 400)
            upper = random.randint(600, 1000)
            start_time = time.time()
            totals = 0
            max = 0
            self._log_info("Injecting %s points for minute %s", points, minute)
            start = time.time()
            for i in range(points):
                val = random.randint(lower, upper)
                if val > max:
                    max = val
                totals += val
                # always use the `now` as time stamp so we have control which values are lying in this minute
                aggregator.measure(key, "random", "mode:test", val, timestamp=stamp)
                if time.time() - start > 5:
                    self._log_info("Injected %d%% points for minute %s", (i / points) * 100, minute)
                    start = time.time()

            self._log_info("Finished %s points for minute %s", points, minute)
            rate = points / (time.time() - start_time)
            # 4b- Keep track of the actual reported values for comparison later on with the expected values.
            actuals.append({"rate": rate, "avg": totals / points, "stamp": stamp})

        # 5- force last push to force flush last minute data
        stamp = now + minutes * 60
        aggregator.measure(key, "random", "mode:test", 0, timestamp=stamp)

        # 6- simulate a working influx dumper dumper
        # 6a- drop the test influx database
        influxdb.drop_database(self.TEST_INFLUX_DB)
        # 6b- Get the redis host and port, so the dumper can simulate `discovering` it on the network
        redis_host = j.sal.nettools.getHostByName(aggregator.redis.connection_pool.connection_kwargs["host"])
        port = aggregator.redis.connection_pool.connection_kwargs["port"]

        # force the dumper to find the test redis instance. By allowing it to only search the given redis host
        # for active redis instances.

        dumper = InfluxDumper(influxdb, self.TEST_INFLUX_DB, cidr=redis_host, ports=[port])
        # DO NOT CALL dumper.start() or the actuall dumper worker processes will start. Instead we simulate the process
        # by calling the dumper.dump method directly. given the `found` redis connection. Read InfluxDumper doc string
        # for more info

        dumper.dump(aggregator.redis)

        # now we need to query the influx-db connection for data and then compare it with the expected results.
        influxdb.switch_database(self.TEST_INFLUX_DB)
        influx_key = "%s_%s_m" % (aggregator.nodename, key)
        result = influxdb.query('select * from "%s" where time >= %ds and time <= %ds' % (influx_key, now - 60, stamp))

        # build report
        return self._buildReport(actuals, result.get_points(influx_key))

    #
    # def logstest(self):
    #     #some fast perf test
    #     #get logs in & out
    #     #check we cannot put more values in redis as possible (the defense mechanismes)
    #     raise j.exceptions.NotImplemented()
    #
    # def ecotest(self):
    #     raise j.exceptions.NotImplemented()
    #


if __name__ == "__main__":
    from AggregatorClient import AggregatorClient

    redis = j.clients.redis.get("127.0.0.1", 6379)
    influx = j.clients.influxdb.get()
    aggregator = AggregatorClient(redis, "mynode")
    tester = AggregatorClientTest()
    tester.statstest(aggregator, influx)
