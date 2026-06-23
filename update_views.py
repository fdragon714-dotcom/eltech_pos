import re

with open('c:/Users/claud/pos_eltech/pos/posApp/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 84:  # Right before filter_chart = request.GET.get
        new_lines.append("    if request.user.is_superuser:\n")
        new_lines.append("        base_sales_qs = Sales.objects.all()\n")
        new_lines.append("    else:\n")
        new_lines.append("        base_sales_qs = Sales.objects.filter(cashier=request.user)\n\n")
    
    if 90 <= i <= 205:
        line = line.replace('Sales.objects.filter', 'base_sales_qs.filter')
    
    new_lines.append(line)

with open('c:/Users/claud/pos_eltech/pos/posApp/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
