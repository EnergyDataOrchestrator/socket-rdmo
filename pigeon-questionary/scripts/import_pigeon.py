from django.core.management import call_command

# Define the files in their required hierarchical order
files = [
    '/vol/rdmo-addons/pigeon_attributes.xml',
    '/vol/rdmo-addons/pigeon_options.xml',
    '/vol/rdmo-addons/pigeon_sections.xml',
    '/vol/rdmo-addons/pigeon_catalog.xml'
]

for file_path in files:
    print(f"Importing: {file_path}")
    try:
        # call_command runs the internal management command
        call_command('import', file_path)
    except Exception as e:
        print(f"Error importing {file_path}: {e}")

print("Import process completed.")