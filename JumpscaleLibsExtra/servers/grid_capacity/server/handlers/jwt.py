import jose.jwt
from Jumpscale import j

from ..models import Farmer


IYO_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n2
7MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny6
6+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv
-----END PUBLIC KEY-----
"""


def validate_farmer_id(farmer_id):
    # refresh jwt is needed otherwise return original
    jwt = j.clients.itsyouonline.refresh_jwt_token(farmer_id)
    token = jose.jwt.decode(jwt, IYO_PUBLIC_KEY)
    iyo_organization = token["scope"][0].replace("user:memberof:", "")
    farmers = Farmer.objects(iyo_organization=iyo_organization)
    if not farmers:
        return FarmerInvalid()

    return iyo_organization


class FarmerInvalid(RuntimeError):
    pass
