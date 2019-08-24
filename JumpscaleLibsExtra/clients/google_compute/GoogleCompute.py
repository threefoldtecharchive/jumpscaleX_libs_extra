from Jumpscale import j
from pprint import pprint

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# https://cloud.google.com/compute/docs/reference/latest/instances/list
JSBASE = j.baseclasses.object_config


class GoogleCompute(JSBASE):
    _SCHEMATEXT = """
    @url = jumpscale.googlecompute.client
    name* = "" (S)
    zone = "us-east1-b" (S)
    projectName = "constant-carver-655" (S)
    """

    def _init(self, zone=None, projectName=None):

        self.credentials = None
        self.service = None
        self._projects = None
        self._instances = None
        self._images = {}
        self.zone = zone
        self.projectName = projectName
        self.credentials = GoogleCredentials.get_application_default()
        self.service = discovery.build("compute", "v1", credentials=self.credentials)

    @property
    def project(self):
        if self._instances is None:
            request = self.service.projects().get(project=self.projectName)
            response = request.execute()
            self._instances = response
        return self._instances

    def instances_list(self):
        request = self.service.instances().list(project=self.projectName, zone=self.zone)
        res = []
        while request is not None:
            response = request.execute()
            if not "items" in response:
                return []
            for instance in response["items"]:
                # pprint(instance)
                res.append(instance)
            request = self.service.instances().list_next(previous_request=request, previous_response=response)
        return res

    def images_list(self):
        """
        list private ! images
        """
        request = self.service.images().list(project=self.projectName)
        res = []
        while request is not None:
            response = request.execute()
            if not "items" in response:
                return []
            for image in response["items"]:
                res.append(image)
                pprint(image)
            request = self.service.images().list_next(previous_request=request, previous_response=response)

        return res

    @property
    def images_ubuntu(self):
        """https://cloud.google.com/compute/docs/images"""
        if "ubuntu" not in self._images:
            res = []
            for family in ["ubuntu-1604-lts", "ubuntu-1704"]:
                image_response = self.service.images().getFromFamily(project="ubuntu-os-cloud", family=family).execute()
                res.append(image_response["selfLink"])
                self._images["ubuntu"] = res
        return self._images["ubuntu"]

    def imageurl_get(self, name="ubuntu - 1604"):
        for item in self.images_ubuntu:
            if item.lower().find("ubuntu-1604") is not -1:
                return item
        raise j.exceptions.Base("did not find image: %s" % name)

    def instance_create(
        self,
        name="builder",
        machineType="n1-standard-1",
        osType="ubuntu-1604",
        startupScript="",
        storageBucket="",
        sshkeyname="",
    ):
        """
        @param sshkeyname is your name for your ssh key, if not specified will use your preferred key from j.core.myenv.config["ssh"]["sshkeyname"]
        """
        source_disk_image = self.imageurl_get()
        # Configure the machine
        machine_type = "zones/%s/machineTypes/%s" % (self.zone, machineType)
        config = {
            "name": name,
            "machineType": machine_type,
            # Specify the boot disk and the image to use as a source.
            "disks": [{"boot": True, "autoDelete": True, "initializeParams": {"sourceImage": source_disk_image}}],
            # Specify a network interface with NAT to access the public
            # internet.
            "networkInterfaces": [
                {
                    "network": "global/networks/default",
                    "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
                }
            ],
            # Allow the instance to access cloud storage and logging.
            "serviceAccounts": [
                {
                    "email": "default",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_write",
                        "https://www.googleapis.com/auth/logging.write",
                    ],
                }
            ],
            # Metadata is readable from the instance and allows you to
            # pass configuration from deployment scripts to instances.
            "metadata": {
                "items": [
                    {"key": "ssh-keys", "value": sshkeys},
                    {
                        # Startup script is automatically executed by the
                        # instance upon startup.
                        "key": "startup-script",
                        "value": startupScript,
                    },
                    {"key": "bucket", "value": storageBucket},
                ]
            },
        }

        self._log_debug(config)

        res = self.service.instances().insert(project=self.projectName, zone=self.zone, body=config).execute()
        return res

    def add_sshkey(self, machinename, username, keyname):
        """
        instance: instance name
        username: a username for that key
        key: the pub key you want to allow (is name of key on your system, needs to be loaded in ssh-agent)

        @TODO: *1 I am sure a key can be loaded for all vmachines which will be created, not just for this 1
        @TODO: *1 what does instance mean? is that the name?

        """
        # get pub key from local FS
        keypath = j.clients.ssh.sshkey_path_get("kds")
        key = j.sal.fs.readFile(keypath + ".pub")

        # get old instance metadata
        request = self.service.instances().get(zone=self.zone, project=self.projectName, instance=instance)
        res = request.execute()
        metadata = res.get("metadata", {})
        # add the key
        items = metadata.get("items", [])
        for item in items:
            if item["key"] == "ssh-keys":
                item["value"] = "{} \n{}:{}".format(item["value"], username, key)
                break
            else:
                items.append({"key": "ssh-keys", "value": "{}:{}".format(username, key)})
        # Set instance metadata
        metadata["items"] = items
        request = self.service.instances().setMetadata(
            zone=self.zone, project=self.projectName, instance=instance, body=metadata
        )
        request.execute()

        # TODO:*1 we need to check for duplicates

    def machinetypes_list(self):
        request = self.service.machineTypes().list(project=self.projectName, zone=self.zone)
        res = []
        while request is not None:
            response = request.execute()
            if not "items" in response:
                return []
            for instance in response["items"]:
                # pprint(instance)
                res.append(instance)
            request = self.service.instances().list_next(previous_request=request, previous_response=response)
        return res

    @property
    def sshkeys(self):
        self.project
        res = []
        for item in self.project["commonInstanceMetadata"]["items"]:
            if item["key"] == "sshKeys":
                res.append(item["value"])

        return res
