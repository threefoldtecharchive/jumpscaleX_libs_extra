from flask_mongoengine import MongoEngine, Pagination
from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    ListField,
    PointField,
    ReferenceField,
    StringField,
)

db = MongoEngine()


class NodeRegistration:
    @staticmethod
    def list(country=None):
        """
        list all the capacity, optionally filter per country.
        returns a list of capacity object

        :param country: [description], defaults to None
        :param country: [type], optional
        :return: sequence of Capacity object
        :rtype: sequence
        """
        filter = {}
        if country:
            filter["location__country"] = country

        for capacity in Capacity.objects(**filter):
            yield capacity

    @staticmethod
    def get(node_id):
        """
        return the capacity for a single node

        :param node_id: unique node ID
        :type node_id: str
        :return: Capacity object
        :rtype: Capacity
        """
        capacity = Capacity.objects(pk=node_id)
        if not capacity:
            raise NodeNotFoundError("node '%s' not found" % node_id)
        return capacity[0]

    @staticmethod
    def search(country=None, mru=None, cru=None, hru=None, sru=None, farmer=None, **kwargs):
        """
        search based on country and minimum resource unit available

        :param country: if set, search for capacity in the specified country, defaults to None
        :param country: str, optional
        :param mru: minimal memory resource unit, defaults to None
        :param mru: int, optional
        :param cru: minimal CPU resource unit, defaults to None
        :param cru: int, optional
        :param hru: minimal HDD resource unit, defaults to None
        :param hru: int, optional
        :param sru: minimal SSD resource unit defaults to None
        :param sru: int, optional
        :return: sequence of Capacity object matching the query
        :rtype: sequence
        """
        query = {}
        if country:
            query["location__country"] = country
        if farmer:
            query["farmer"] = farmer
        if mru:
            query["total_resources__mru__gte"] = mru
        if cru:
            query["total_resources__cru__gte"] = cru
        if hru:
            query["total_resources__hru__gte"] = hru
        if sru:
            query["total_resources__sru__gte"] = sru

        nodes = Capacity.objects(**query)
        if kwargs.get("order"):
            nodes = nodes.order_by(kwargs.get("order"))

        page = kwargs.get("page")
        per_page = kwargs.get("per_page", 50)
        if page:
            return Pagination(nodes, page, per_page)

        return nodes

    @staticmethod
    def all_countries():
        """
        yield all the country present in the database

        :return: sequence of country
        :rtype: sequence of string
        """
        capacities = Capacity.objects.only("location__country").order_by("location__country")
        countries = set()
        for cap in capacities:
            if cap.location:
                countries.add(cap.location.country)
        return list(countries)


class FarmerRegistration:
    @staticmethod
    def create(name, iyo_account, wallet_addresses=None):
        return Farmer(name=name, iyo_account=iyo_account, wallet_addresses=wallet_addresses)

    @staticmethod
    def register(farmer):
        if not isinstance(farmer, Farmer):
            raise j.exceptions.Value("farmer need to be a Farmer object, not %s" % type(farmer))
        farmer.save()

    @staticmethod
    def list(name=None, organization=None, **kwargs):
        query = {}
        if name:
            query["name"] = name
        if organization:
            query["organization"] = organization
        farmers = Farmer.objects(**query)

        if kwargs.get("order"):
            farmers = farmers.order_by(kwargs.get("order"))

        return farmers

    @staticmethod
    def get(id):
        farmer = Farmer.objects(pk=id)
        if not farmer:
            raise FarmerNotFoundError("farmer '%s' not found" % id)
        return farmer[0]


class Location(EmbeddedDocument):
    """
    Location of a node
    """

    continent = StringField(default="")
    country = StringField(default="")
    city = StringField(default="")
    longitude = FloatField(default=0.0)
    latitude = FloatField(default=0.0)


class Farmer(db.Document):

    """
    Represent a threefold Farmer
    """

    iyo_organization = StringField(primary_key=True)
    name = StringField()
    wallet_addresses = ListField(StringField())
    location = EmbeddedDocumentField(Location)


class Resources(EmbeddedDocument):
    cru = FloatField(default=0.0)
    mru = FloatField(default=0.0)
    hru = FloatField(default=0.0)
    sru = FloatField(default=0.0)


class Capacity(db.Document):
    """
    Represent the resource units of a zero-os node
    """

    node_id = StringField(primary_key=True)
    location = EmbeddedDocumentField(Location)
    farmer = ReferenceField(Farmer)
    total_resources = EmbeddedDocumentField(Resources)
    reserved_resources = EmbeddedDocumentField(Resources)
    used_resources = EmbeddedDocumentField(Resources)
    robot_address = StringField()
    os_version = StringField()
    uptime = IntField()
    updated = DateTimeField(required=True)


class FarmerNotFoundError(KeyError):
    pass


class NodeNotFoundError(KeyError):
    pass
