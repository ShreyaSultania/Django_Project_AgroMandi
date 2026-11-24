import os
import re
import sys
import errno
from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand

class Command(StaticfilesRunserverCommand):
    default_addr = "127.0.0.1"
    default_port = os.getenv("PORT", "5001")

    def handle(self, *args, **options):
        addrport = options.get("addrport")
        target_port = os.getenv("PORT", "5001")

        if addrport:
            # Detect port 5000 in any format (e.g. "5000", "127.0.0.1:5000", "0.0.0.0:5000", "localhost:5000")
            if addrport == "5000":
                options["addrport"] = f"{self.default_addr}:{target_port}"
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[Notice] Port 5000 is reserved by Windows service (HelpWire) on this PC.\n"
                        f"         Redirecting automatically to http://127.0.0.1:{target_port}/\n"
                    )
                )
            elif addrport.endswith(":5000"):
                host = addrport.rsplit(":", 1)[0]
                options["addrport"] = f"{host}:{target_port}"
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[Notice] Port 5000 is reserved by Windows service (HelpWire) on this PC.\n"
                        f"         Redirecting automatically to http://{host}:{target_port}/\n"
                    )
                )

        return super().handle(*args, **options)
