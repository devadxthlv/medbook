import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Waiting for database...")
        db_conn = None
        attempts = 0

        while not db_conn:
            try:
                db_conn = connections["default"]
                db_conn.cursor()
            except OperationalError:
                attempts += 1
                if attempts > 30:
                    self.stdout.write(
                        self.style.ERROR("DB not available after 30 attempts. Exiting.")
                    )
                    raise
                self.stdout.write(f"DB unavailable, waiting 1s... (attempt {attempts})")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
