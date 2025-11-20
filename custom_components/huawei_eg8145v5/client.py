import re
import json
import logging
import requests
import hashlib
import base64 as b64
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)
_WHITESPACE_RX = re.compile(r"\s")

def base64(s):
    """Base64 encode a string, removing all whitespace from the output."""
    encoded = b64.encodebytes(s.encode()).decode()
    return _WHITESPACE_RX.sub("", encoded)

def sha256(s):
    """Encode a string into its SHA256 hex digest."""
    return hashlib.sha256(s.encode()).hexdigest()

class HuaweiEG8145V5Client:
    def __init__(self, host, username, password, verify_ssl=False):
        """
        A client for the Huawei EG8145V5 router.
        """
        self.host = host
        self.username = username
        self._password = password
        self.verify_ssl = verify_ssl
        self._session = requests.Session()

    @property
    def password(self):
        return self._password

    def login(self):
        """Log the client in to the router."""
        # 0. Initialize session
        try:
            self._get("/")
        except Exception:
            pass

        # 1. Get Token
        try:
            response = self._post("/asp/GetRandCount.asp")
            token = response.text.replace('\ufeff', '').strip()
        except Exception as e:
            _LOGGER.error(f"Failed to get token: {e}")
            return False

        # 2. Prepare Login
        # JS: var cookie2 = "Cookie=body:" + "Language:" + Language + ":" + "id=-1;path=/";
        # document.cookie = cookie2;
        # The cookie name seems to be "Cookie" and value "body:Language:english:id=-1"
        # But requests session handles cookies. We might need to set it manually if the server expects it *before* login.
        # However, usually cookies are set by server or client sets them.
        # Here JS sets it. So we must set it.
        
        # We'll set it in the session.
        # Note: The cookie name is likely just "Cookie" based on the JS string "Cookie=..."
        # But "Cookie" is a reserved header name. 
        # If document.cookie = "Cookie=..." then the cookie name is "Cookie".
        self._session.cookies.set("Cookie", "body:Language:english:id=-1", domain=self.host, path="/")
        
        # 3. Post Login
        data = {
            "UserName": self.username,
            "PassWord": base64(self._password), # Base64 encoded, NO SHA256
            "Language": "english",
            "x.X_HW_Token": token
        }
        
        # The JS uses Form.submit(), which is a form-urlencoded POST.
        # requests.post(data=...) does form-urlencoded.
        
        # Set cookie and headers
        self._session.cookies.set("Cookie", "body:Language:english:id=-1", domain=self.host, path="/")
        
        headers = {
            "Referer": f"http://{self.host}/",
            "Origin": f"http://{self.host}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = self._post("/login.cgi", data=data, headers=headers)
            # Check if login was successful.
            # Usually it redirects or returns a page.
            # If we are redirected to Main.asp or similar, it's success.
            if "login.asp" in response.url and "Err" in response.url:
                _LOGGER.error("Login failed: Redirected to login error page")
                return False
            
            return True
        except Exception as e:
            _LOGGER.error(f"Login failed: {e}")
            return False

    def logout(self):
        """Log the client out of the router."""
        try:
            response = self._post("/logout.cgi") # Guessing logout URL
            return response.status_code
        except Exception:
            return False

    def get_device_count(self) -> int:
        devices = self.get_active_devices()
        return len(devices)

    def get_device_info(self):
        """Get router device info (uptime, model, CPU, memory, etc)"""
        try:
            response = self._get("/html/ssmp/deviceinfo/deviceinfo.asp")
            if response.status_code != 200:
                return {}
            
            import re
            
            # Extract device info from JavaScript variable
            # Pattern: new stDeviceInfo("domain","SerialNumber","HardwareVersion","SoftwareVersion","ModelName","VendorID","ReleaseTime","Mac","Description","ManufactureInfo","DeviceAlias")
            device_pattern = r'new stDeviceInfo\(([^)]+)\)'
            device_match = re.search(device_pattern, response.text, re.IGNORECASE)
            
            # Extract CPU and memory usage
            cpu_match = re.search(r"var cpuUsed = '(\d+)%'", response.text)
            mem_match = re.search(r"var memUsed = '(\d+)%'", response.text)
            uptime_match = re.search(r"var dev_uptime = '(\d+)'", response.text)

            info = {}
            if device_match:
                params = re.findall(r'"([^"]*)"', device_match.group(1))
                if len(params) >= 10:
                    info = {
                        "model": params[4].replace("\\x20", " "),
                        "serial_number": params[1],
                        "hardware_version": params[2].replace("\\x2e", "."),
                        "software_version": params[3],
                        "description": params[8].replace("\\x20", " ").replace("\\x2b", "+").replace("\\x2f", "/").replace("\\x3a", ":").replace("\\x28", "(").replace("\\x29", ")") if len(params) > 8 else "",
                        "mac": params[7].replace("\\x3a", ":") if len(params) > 7 else "",
                        "cpu_usage": cpu_match.group(1) if cpu_match else "",
                        "memory_usage": mem_match.group(1) if mem_match else "",
                        "uptime": uptime_match.group(1) if uptime_match else ""
                    }
            
            return info if info else {}
            
        except Exception as e:
            _LOGGER.error(f"Failed to get device info: {e}")
            raise  # Let the coordinator handle the error

    def get_active_devices(self):
        devices = self.get_devices()
        return [d for d in devices if d.get("DevStatus", "").upper() == "ONLINE"]

    def get_devices(self):
        """List all devices known to the router."""
        try:
            response = self._get("/html/bbsp/userdevinfo/getuserdevinfo.asp")
            if response.status_code != 200:
                return []
            
            devices = []
            # The response is JavaScript code with device data
            # Format: new stUserDevInfoPTVDF("HostName","DevType","IpAddr","MacAddr","RealMac","Status","Port","ConnectedTime","ActiveTime","Domain")
            
            import re
            # Find all device entries
            pattern = r'new stUserDevInfo(?:PTVDF)?\(([^)]+)\)'
            matches = re.findall(pattern, response.text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                # Parse the parameters (they're JavaScript strings with escaped characters)
                params = re.findall(r'"([^"]*)"', match)
                if len(params) >= 9:
                    # Decode escaped hex characters
                    hostname = params[0].replace("\\x2d", "-").replace("\\x2e", ".").replace("\\x5f", "_")
                    device_type = params[1].replace("\\x2d", "-").replace("\\x2e", ".")
                    ip_addr = params[2].replace("\\x2e", ".").replace("\\x3a", ":")
                    mac_addr = params[3].replace("\\x3a", ":")
                    real_mac = params[4].replace("\\x3a", ":") if len(params) > 4 else mac_addr
                    status = params[5] if len(params) > 5 else ""
                    port = params[6] if len(params) > 6 else ""
                    connected_time = params[7].replace("\\x2c", ",").replace("\\x3a", ":") if len(params) > 7 else ""
                    active_time = params[8].replace("\\x2c", ",").replace("\\x3a", ":") if len(params) > 8 else ""
                    
                    # Skip IPv6 addresses for cleaner device list
                    if ip_addr.startswith("fe80::"):
                        continue
                    
                    device = {
                        "HostName": hostname if hostname != "--" else "",
                        "DevType": device_type if device_type != "--" else "",
                        "IpAddr": ip_addr,
                        "MacAddress": mac_addr,
                        "RealMacAddress": real_mac,
                        "DevStatus": status,
                        "Port": port,
                        "ConnectedTime": connected_time,
                        "ActiveTime": active_time if active_time != "--" else "",
                        "Active": status.upper() == "ONLINE",
                    }
                    devices.append(device)
            
            return devices
        except Exception as e:
            _LOGGER.error(f"Failed to get devices: {e}")
            raise  # Let the coordinator handle the error

    def _request(self, method, path, **kwargs):
        url = f"http://{self.host}/{path.lstrip('/')}"
        kwargs.setdefault("timeout", 10)
        kwargs.setdefault("verify", self.verify_ssl)

        response = self._session.request(method, url, **kwargs)
        return response

    def _get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def _post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

