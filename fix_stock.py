from posApp.models import Products, purchaseItems, salesItems, Returns
from django.db.models import Sum

products = Products.objects.all()
changed = 0
for p in products:
    pur = purchaseItems.objects.filter(product_id=p).aggregate(s=Sum('qty'))['s'] or 0
    sal = salesItems.objects.filter(product_id=p).aggregate(s=Sum('qty'))['s'] or 0
    ret = Returns.objects.filter(product_id=p).aggregate(s=Sum('qty'))['s'] or 0
    actual = pur - sal - ret
    if actual < 0: actual = 0
    if p.stock != actual:
        print('Fixed', p.name, 'from', p.stock, 'to', actual)
        p.stock = actual
        p.save()
        changed += 1

print('Total fixed:', changed)
