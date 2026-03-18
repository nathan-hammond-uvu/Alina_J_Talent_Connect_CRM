"""Compatibility shim – ClientService is an alias for CreatorService."""
from crm.services.creator_service import CreatorService

# Keep the old name so any code that imports ClientService still works.
ClientService = CreatorService
