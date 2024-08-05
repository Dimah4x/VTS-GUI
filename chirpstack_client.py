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

    def add_device(self, dev_eui, name, device_profile_id, application_id, nwk_key, device_type):
        device = api.Device(
            dev_eui=dev_eui,
            name=name,
            description=device_type,  # Set the description to device type
            application_id=application_id,
            device_profile_id=device_profile_id
        )
        req = api.CreateDeviceRequest(device=device)
        self.device_service.Create(req, metadata=self._get_metadata())

        keys_req = api.CreateDeviceKeysRequest(
            device_keys=api.DeviceKeys(
                dev_eui=dev_eui,
                nwk_key=nwk_key
            )
        )
        self.device_service.CreateKeys(keys_req, metadata=self._get_metadata())

    def get_device_profiles(self, tenant_id):
        req = api.ListDeviceProfilesRequest(
            limit=100,  # Set the limit as needed
            tenant_id=tenant_id  # Specify the tenant ID if applicable
        )
        auth_token = self._get_metadata()
        resp = self.device_profile_service.List(req, metadata=auth_token)
        return resp.result

    def get_device_status(self, dev_eui, application_id):
        try:
            devices = self.list_devices(application_id)
            device = next((d for d in devices if d.dev_eui == dev_eui), None)

            if device:
                print(f"Device object: {device}")
                last_seen = device.last_seen_at
                if last_seen:
                    last_seen_dt = datetime.fromtimestamp(last_seen.seconds)
                    is_online = datetime.now() - last_seen_dt < timedelta(minutes=10)
                else:
                    last_seen_dt = "Unknown"
                    is_online = False

                return {"last_seen": last_seen_dt, "is_online": is_online}
            else:
                print(f"No device found with dev_eui: {dev_eui}")
                return {"last_seen": "Unknown", "is_online": False}
        except grpc.RpcError as e:
            print(f"Error getting device status for {dev_eui}: {e.details()}")
            return {"last_seen": "Unknown", "is_online": False}

    # def get_device_link_metrics(self, dev_eui):
    #     client = self.device_service
    #     auth_token = self._get_metadata()
    #     req = api.GetDeviceLinkMetricsRequest(dev_eui=dev_eui)
    #
    #     try:
    #         resp = client.GetLinkMetrics(req, metadata=auth_token)
    #         metrics = {
    #             "rssi": resp.rx_info[0].rssi if resp.rx_info else "N/A",
    #             "snr": resp.rx_info[0].snr if resp.rx_info else "N/A",
    #         }
    #         return metrics
    #     except grpc.RpcError as e:
    #         print(f"Error fetching device link metrics for {dev_eui}: {e.details()}")
    #         return {}

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