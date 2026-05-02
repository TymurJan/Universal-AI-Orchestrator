import hashlib
import platform
import subprocess
import uuid
import sys
import os

class LicenseManager:
    """
    Handles Hardware ID (HWID) fingerprinting and license verification.
    Ensures 1 license = 1 machine.
    """
    
    def __init__(self):
        self.hwid = self._generate_hwid()
        self.license_file = "license.key"

    def _generate_hwid(self) -> str:
        """
        Generates a unique hardware fingerprint based on system components.
        """
        items = [
            platform.node(),            # Computer Name
            platform.processor(),       # Processor Type
            str(uuid.getnode()),        # MAC Address
            platform.machine()          # Arch
        ]
        
        # Windows-specific: Try to get Motherboard serial
        if sys.platform == "win32":
            try:
                cmd = "wmic baseboard get serialnumber"
                serial = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
                items.append(serial)
            except:
                pass

        raw_id = "|".join(items)
        return hashlib.sha256(raw_id.encode()).hexdigest()

    def verify_license(self, key: str) -> bool:
        """
        Verify the provided key. If a binding exists, ensure it matches this HWID.
        """
        binding_file = ".license_binding"
        if os.path.exists(binding_file):
            with open(binding_file, "r") as f:
                stored_binding = f.read().strip()
            # The binding is Hash(Key + HWID)
            expected_binding = hashlib.sha256((key + self.hwid).encode()).hexdigest()
            return stored_binding == expected_binding
        
        # If no binding, it needs activation (handled in orchestrator)
        return len(key) >= 12

    def activate_locally(self, key: str):
        """
        Binds the key to this hardware locally.
        """
        binding_file = ".license_binding"
        binding = hashlib.sha256((key + self.hwid).encode()).hexdigest()
        with open(binding_file, "w") as f:
            f.write(binding)

    def get_tier(self, key: str) -> str:
        """
        Returns the license tier: 'audit', 'core', or 'enterprise'.
        """
        key_up = key.upper()
        if "ENT" in key_up: return "enterprise"
        if "AUD" in key_up: return "audit"
        return "core"

if __name__ == "__main__":
    lm = LicenseManager()
    print(f"Machine HWID: {lm.hwid}")
