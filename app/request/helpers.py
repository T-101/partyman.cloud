from copy import deepcopy

from cloudflare import Cloudflare
import requests
from cloudflare.types.dns import ARecord
from requests.auth import HTTPBasicAuth

from django.utils import timezone

from request.models import CloudflareZone, UpCloudZone, Request, SSHKeys, AppSettings

BASE_UPCLOUD_PAYLOAD = {
    "server": {
        "zone": "",
        "title": "",
        "hostname": "",
        "plan": "",
        "metadata": "yes",
        "user_data": "",
        "storage_devices": {
            "storage_device": [
                {
                    "action": "clone",
                    "storage": "01000000-0000-4000-8000-000020080100",
                    "encrypted": "yes",
                    "title": "PartyMan Debian 13",
                }
            ]
        },
        "networking": {
            "interfaces": {
                "interface": [
                    {
                        "ip_addresses": {"ip_address": [{"family": "IPv4"}]},
                        "type": "public",
                    }
                ]
            }
        },
        "login_user": {
            "username": "root",
            "ssh_keys": {
                "ssh_key": []
            }
        }
    }
}


def get_upcloud_auth() -> HTTPBasicAuth:
    settings = AppSettings.load()
    return HTTPBasicAuth(settings.upcloud_api_username, settings.upcloud_api_password)


def update_cloudflare_zones() -> None:
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return
    client = Cloudflare(api_token=settings.cloudflare_api_token)
    page = client.zones.list()
    cloudflare_ids = {zone.id for zone in page.result}
    existing_ids = set(CloudflareZone.objects.values_list("cloudflare_id", flat=True))
    bulk_zones = []
    for zone in page.result:
        if not zone.id in existing_ids:
            bulk_zones.append(CloudflareZone(name=zone.name, cloudflare_id=zone.id, public=False))
    CloudflareZone.objects.bulk_create(bulk_zones)

    ids_to_hide = existing_ids - cloudflare_ids
    if ids_to_hide:
        CloudflareZone.objects.filter(cloudflare_id__in=ids_to_hide).update(visible=False)


def get_cloudflare_dns_records(zone: CloudflareZone) -> list[ARecord]:
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return
    client = Cloudflare(api_token=settings.cloudflare_api_token)
    records = client.dns.records.list(zone_id=zone.cloudflare_id)
    return records.result


def create_cloudflare_dns_entry(zone: CloudflareZone, domain: str, ip_address: str) -> str:
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return ""
    client = Cloudflare(api_token=settings.cloudflare_api_token)
    domain = f"{domain}.{zone.name}"
    dns_records = get_cloudflare_dns_records(zone)
    if domain in [record.name for record in dns_records]:
        raise ValueError("DNS record already exists")
    res = client.dns.records.create(zone_id=zone.cloudflare_id, name=domain,
                                    type="A", content=ip_address, ttl=1)
    return res.id


def delete_cloudflare_dns_entry(zone: CloudflareZone, dns_record_id: str) -> str:
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return ""
    client = Cloudflare(api_token=settings.cloudflare_api_token)
    res = client.dns.records.delete(zone_id=zone.cloudflare_id, dns_record_id=dns_record_id)
    return res.id


def update_upcloud_zones():
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return
    url = settings.upcloud_api_url + "/1.3/zone"
    res = requests.get(url, auth=get_upcloud_auth()).json()
    upcloud_zone_names = [x.get("id") for x in res.get("zones").get("zone")]
    existing_zone_names = set(UpCloudZone.objects.values_list("name", flat=True))
    bulk_zones = []
    for zone in upcloud_zone_names:
        if zone not in existing_zone_names:
            bulk_zones.append(UpCloudZone(name=zone))
    UpCloudZone.objects.bulk_create(bulk_zones)

    zones_to_delete = existing_zone_names - set(upcloud_zone_names)
    if zones_to_delete:
        UpCloudZone.objects.filter(name__in=zones_to_delete).update(visible=False)


def create_upcloud_server(request: Request) -> (tuple[str, str]):
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return "", ""

    def make_payload():
        payload = deepcopy(BASE_UPCLOUD_PAYLOAD)
        payload["server"]["zone"] = request.upcloud_zone.name
        payload["server"]["title"] = request.domain + "." + request.cloudflare_zone.name
        payload["server"]["hostname"] = request.domain + "." + request.cloudflare_zone.name
        payload["server"]["plan"] = request.upcloud_plan.name
        payload["server"]["user_data"] = get_init_script(request)
        payload["server"]["login_user"]["ssh_keys"]["ssh_key"] = list(
            SSHKeys.objects.values_list("public_key", flat=True))
        return payload

    if not request.upcloud_zone.name or not request.cloudflare_zone or not request.domain or not request.upcloud_plan:
        raise ValueError("Zone or Plan not set")

    if not SSHKeys.objects.count():
        raise ValueError("No SSH keys available")

    url = settings.upcloud_api_url + "/1.3/server"

    res = requests.post(url, auth=get_upcloud_auth(), json=make_payload()).json()
    request.upcloud_server_id = res["server"]["uuid"]
    request.upcloud_server_address = res["server"]["ip_addresses"]["ip_address"][0]["address"]
    request.activated = timezone.now()
    request.save()
    return request.upcloud_server_id, request.upcloud_server_address


def stop_upcloud_server(request: Request) -> int:
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return
    url = settings.upcloud_api_url + f"/1.3/server/{request.upcloud_server_id}/stop"
    res = requests.post(url, auth=get_upcloud_auth())
    return res.status_code


def delete_upcloud_server(request: Request) -> int:
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return
    url = settings.upcloud_api_url + f"/1.3/server/{request.upcloud_server_id}?storages=1&backups=delete"
    res = requests.delete(url, auth=get_upcloud_auth())
    request.deactivated = timezone.now()
    request.save()
    return res.status_code


def get_init_script(request: Request) -> str:
    settings = AppSettings.load()
    if settings.sandbox_mode:
        return ""
    res = requests.get(settings.init_script_url)
    script = res.text
    domain = f"{request.domain}.{request.cloudflare_zone.name}"
    script = script.replace("$IP", domain)
    script += f"\ncertbot --nginx -d {domain} --register-unsafely-without-email --agree-tos --non-interactive\n"
    script += "sed -i -e 's/443 ssl/443 ssl http2/' /etc/nginx/sites-available/partyman.conf\n"
    script += "service nginx reload\n"
    script += "cd /opt/\n"
    script += "git clone https://gitlab.com/T-101/pms3.git partyman\n"
    script += "cd /opt/partyman\n"
    script += f"./init_partyman.sh {domain}\n"
    return script
