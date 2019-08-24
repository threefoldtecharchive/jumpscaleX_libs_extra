from Jumpscale import j
from tools.capacity.registration import Capacity, Location
import random

continents = ["Europe", "Africa", "Asia", "America", "Oceania"]
countries = ["Belgium", "Egypt", "France", "Germany"]
cities = ["Liege", "Bruxelles", "Paris", "Berlin", "Cairo", "El Gouna"]
register = j.tools.capacity.registration

for i in range(500):
    cap = Capacity(
        j.data.idgenerator.generateXCharID(12),
        None,
        Location(random.choice(continents), random.choice(countries), random.choice(cities), 0, 0),
        random.randint(1, 500),
        random.randint(1, 2000),
        random.randint(1, 90000),
        random.randint(1, 10000),
        "http://localhost:6600",
        "heads/v1.2.2 6b693a496de940b26ee1a2356b67f7d65767c13f",
    )
    register.nodes.register(cap)
    print("capacity registed %d" % i)
