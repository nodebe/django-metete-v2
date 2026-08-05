.PHONY: default-roles
default_roles:
	@echo "Updating Roles"
	python manage.py create_default_permissions
	python manage.py create_default_roles
	@echo "Roles and Permissions updated successfully."

.PHONY: default-admin
default_admin:
	@echo "Creating Default Admin"
	python manage.py create_superadmin --first_admin=True
	@echo "Admin created successfully."

.PHONY: create-cities-for-country
seed_default_cities:
	@echo "Updating Nigeria Cities Table"
	python manage.py seed_cities --country "Nigeria"
	@echo "Cities updated successfully."

.PHONY: default-media-types
default_media_types:
	@echo "Updating Media types"
	python manage.py seed_default_media_type

.PHONY: setup-defaults
setup_defaults:
	@echo "Setting up defaults"
	make default_roles
	make default_admin
	make seed_default_cities
	make default_media_types
	@echo "Seeded Successfully."