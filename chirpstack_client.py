import grpc
from chirpstack_api import api


class ChirpStackClient:
    def __init__(self, server, api_token):
        self.server = server
        self.api_token = api_token
        self.channel = grpc.insecure_channel(self.server)
        self.device_service = api.DeviceServiceStub(self.channel)
        self.device_profile_service = api.DeviceProfileServiceStub(self.channel)
        self.application_service = api.ApplicationServiceStub(self.channel)

    def _get_metadata(self):
        return [("authorization", f"Bearer {self.api_token}")]

    def list_devices(self, application_id):
        client = self.device_service
        auth_token = self._get_metadata()
        req = api.ListDevicesRequest()
        req.application_id = application_id
        req.limit = 100

        resp = client.List(req, metadata=auth_token)

        return resp.result

    def remove_device(self, dev_eui):
        client = self.device_service
        auth_token = self._get_metadata()
        req = api.DeleteDeviceRequest(dev_eui=dev_eui)
        client.Delete(req, metadata=auth_token)

    def add_device(self, dev_eui, name, device_profile_id, application_id, nwk_key, description=""):
        device = api.Device(
            dev_eui=dev_eui,
            name=name,
            device_profile_id=device_profile_id,
            application_id=application_id,
            description=description,
            is_disabled=False,
            skip_fcnt_check=False,
            join_eui="0000000000000000"  # Default Join EUI, adjust if needed
        )

        req = api.CreateDeviceRequest(device=device)
        auth_token = self._get_metadata()
        self.device_service.Create(req, metadata=auth_token)

        # Set the NwkKey only
        keys_req = api.CreateDeviceKeysRequest(
            device_keys=api.DeviceKeys(
                dev_eui=dev_eui,
                nwk_key=nwk_key
            )
        )
        self.device_service.CreateKeys(keys_req, metadata=auth_token)

    def get_device_profiles(self, tenant_id):
        req = api.ListDeviceProfilesRequest(
            limit=100,  # Set the limit as needed
            tenant_id=tenant_id  # Specify the tenant ID if applicable
        )
        auth_token = self._get_metadata()
        resp = self.device_profile_service.List(req, metadata=auth_token)
        return resp.result