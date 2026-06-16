import sys
from rdmo.domain.models import Attribute
from rdmo.options.models import OptionSet, Option
from rdmo.questions.models import Section, Catalog

print("--- Script Started ---")
# 1. Fetch Attributes
attributes = Attribute.objects.filter(uri__startswith='https://kit.edu/terms/domain/project/dataset')
print(f"--- Attributes Found: {attributes.count()} ---")
for attr in attributes:
    print(f"Attribute: {attr.uri}")

# 2. Fetch Options
options = Option.objects.filter(uri__startswith='https://kit.edu/terms/options/')
print(f"\n--- Options Found: {options.count()} ---")
for opt in options:
    print(f"Option: {opt.uri}")
optionSets = OptionSet.objects.filter(uri__startswith='https://kit.edu/terms/options/')
print(f"\n--- OptionSets Found: {optionSets.count()} ---")
for ops in optionSets:
    print(f"Section: {ops.uri}")

# 3. Fetch Sections
sections = Section.objects.filter(uri__startswith='https://kit.edu/terms/questions/sections/')
print(f"\n--- Sections Found: {sections.count()} ---")
for sec in sections:
    print(f"Section: {sec.uri}")

# 4. Fetch Catalog
try:
    catalog = Catalog.objects.get(uri='https://kit.edu/terms/questions/catalog/pigeon')
    print(f"\n--- Catalog Found ---")
    print(f"Catalog: {catalog.uri}")
    print(f"Sections linked: {[s.uri for s in catalog.sections.all()]}")
except Catalog.DoesNotExist:
    print("\n--- Catalog NOT found. Check the URI! ---")

print("--- Script Finished ---")