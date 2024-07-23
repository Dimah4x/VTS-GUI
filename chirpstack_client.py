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
        self.gateway_service = api.GatewayServiceStub(self.channel)

    def _get_metadata(self):
        return [("authorization", "Bearer " + self.api_token)]

    def create_device_profile(self, tenant_id, name):
        req = api.CreateDeviceProfileRequest(
            device_profile=api.DeviceProfile(
                tenant_id=tenant_id,
                name=name,
                region=api.DeviceProfile.Region.US915,
                mac_version=api.DeviceProfile.MACVersion.LORAWAN_1_0_3,
                reg_params_revision=api.DeviceProfile.RegParamsRevision.A,
                adr_algorithm_id="default",
                uplink_interval=3600,
                supports_otaa=True
            )
        )
        resp = self.device_profile_service.Create(req, metadata=self._get_metadata())
        return resp.id

    def create_application(self, tenant_id, name):
        req = api.CreateApplicationRequest(
            application=api.Application(
                tenant_id=tenant_id,
                name=name
            )
        )
        resp = self.application_service.Create(req, metadata=self._get_metadata())
        return resp.id

    def create_device(self, application_id, device_profile_id, dev_eui, name):
        req = api.CreateDeviceRequest(
            device=api.Device(
                application_id=application_id,
                device_profile_id=device_profile_id,
                name=name,
                dev_eui=dev_eui
            )
        )
        resp = self.device_service.Create(req, metadata=self._get_metadata())
        return resp.id

    def delete_device(self, dev_eui):
        req = api.DeleteDeviceRequest(
            dev_eui=dev_eui
        )
        self.device_service.Delete(req, metadata=self._get_metadata())

    def list_devices(self, application_id):
        client = self.device_service
        auth_token = self._get_metadata()
        req = api.ListDevicesRequest()
        req.application_id = application_id
        req.limit = 100

        resp = client.List(req, metadata=auth_token)

        return resp.result
        # req = self.device_service.List(
        #     # application_id=application_id,
        #     limit=100
        # )
        # resp = self.device_service.List(req, metadata=self._get_metadata())
        # return resp.result
