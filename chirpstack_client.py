import grpc
from chirpstack_api import api
from datetime import datetime, timedelta
from google.protobuf.timestamp_pb2 import Timestamp



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
        req = api.ListDevicesRequest(application_id=application_id, limit=100)

        try:
            resp = client.List(req, metadata=auth_token)
            # Assuming resp.result contains DeviceListItem objects directly
            return resp.result
        except grpc.RpcError as e:
            print(f"Error fetching devices: {e.details()}")
            return []

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

    # def get_device_status(self, dev_eui):
    #     try:
    #         req = api.GetDeviceRequest(dev_eui=dev_eui)
    #         resp = self.device_service.Get(req, metadata=self._get_metadata())
    #         device = resp.device
    #         print(f"Device object: {device}")
    #         last_seen = device.updated_at  # Assuming updated_at can be used for last_seen
    #         is_online = device.device_status.battery_level > 0  # Assuming battery_level > 0 indicates online status
    #         return {"last_seen": last_seen, "is_online": is_online}
    #     except grpc.RpcError as e:
    #         print(f"Error getting device status for {dev_eui}: {e.details()}")
    #         return {"last_seen": "Unknown", "is_online": False}
    #
    # def get_device_link_metrics(self, dev_eui):
    #     try:
    #         req = api.GetDeviceLinkMetricsRequest(dev_eui=dev_eui)
    #         resp = self.device_service.GetLinkMetrics(req, metadata=self._get_metadata())
    #         print(f"Device {dev_eui} link metrics: {resp}")
    #         return {
    #             "gw_rssi": resp.rx_packets[0].rssi,
    #             "gw_snr": resp.rx_packets[0].snr,
    #             "errors": resp.errors,
    #             "rx_packets": resp.rx_packets
    #         }
    #     except grpc.RpcError as e:
    #         print(f"Error getting device link metrics for {dev_eui}: {e.details()}")
    #         return None

    def enqueue_downlink(self, dev_eui, data, confirmed=True, f_port=10):
        """Enqueue a downlink message to a device."""
        req = api.EnqueueDeviceQueueItemRequest()
        req.queue_item.confirmed = confirmed
        req.queue_item.data = data
        req.queue_item.dev_eui = dev_eui
        req.queue_item.f_port = f_port

        try:
            self.device_service.Enqueue(req, metadata=self._get_metadata())
            return True, "Command enqueued successfully."
        except grpc.RpcError as e:
            return False, f"Failed to enqueue command: {e.details()}"