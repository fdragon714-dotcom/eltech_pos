import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos.settings')
django.setup()

from posApp.models import salesItems

items = salesItems.objects.all()
updated = 0
for item in items:
    if item.hpp == 0 and item.product_id:
        item.hpp = item.product_id.hpp or 0
        item.save()
        updated += 1
print(f"Updated {updated} items with historical HPP.")
