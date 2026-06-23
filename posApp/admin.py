from django.contrib import admin
from django.utils.html import format_html
from django.utils.formats import number_format
from unfold.admin import ModelAdmin, TabularInline

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)

class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].max_length = 20
            self.fields['username'].widget.attrs['maxlength'] = 20
            self.fields['username'].help_text = "Maksimal 20 karakter. Hanya huruf, angka, dan @/./+/-/_."
        if 'email' in self.fields:
            self.fields['email'].max_length = 30
            self.fields['email'].widget.attrs['maxlength'] = 30
            self.fields['email'].help_text = "Maksimal 30 karakter."
        if 'first_name' in self.fields:
            self.fields['first_name'].max_length = 30
            self.fields['first_name'].widget.attrs['maxlength'] = 30
            self.fields['first_name'].help_text = "Maksimal 30 karakter."
        if 'last_name' in self.fields:
            self.fields['last_name'].max_length = 30
            self.fields['last_name'].widget.attrs['maxlength'] = 30
            self.fields['last_name'].help_text = "Maksimal 30 karakter."

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].max_length = 20
            self.fields['username'].widget.attrs['maxlength'] = 20
            self.fields['username'].help_text = "Maksimal 20 karakter. Hanya huruf, angka, dan @/./+/-/_."
        if 'email' in self.fields:
            self.fields['email'].max_length = 30
            self.fields['email'].widget.attrs['maxlength'] = 30
            self.fields['email'].help_text = "Maksimal 30 karakter."
        if 'first_name' in self.fields:
            self.fields['first_name'].max_length = 30
            self.fields['first_name'].widget.attrs['maxlength'] = 30
            self.fields['first_name'].help_text = "Maksimal 30 karakter."
        if 'last_name' in self.fields:
            self.fields['last_name'].max_length = 30
            self.fields['last_name'].widget.attrs['maxlength'] = 30
            self.fields['last_name'].help_text = "Maksimal 30 karakter."

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

from posApp.models import Category, CategoryType, Products, Sales, salesItems, Supplier, Purchases, purchaseItems, WarrantyClaim, Returns


# ─────────────────────────────────────────────────────────
#  Environment Badge (ditampilkan di header sidebar)
# ─────────────────────────────────────────────────────────
def environment_callback(request):
    return ["Development", "warning"]  # bisa diganti "Production", "danger"


# ─────────────────────────────────────────────────────────
#  INLINE: Tipe Merek (tampil di dalam form Merek)
# ─────────────────────────────────────────────────────────
class CategoryTypeInline(TabularInline):
    model = CategoryType
    extra = 1
    fields = ("name", "image")


# ─────────────────────────────────────────────────────────
#  INLINE: Item Terjual (tampil di dalam form Penjualan)
# ─────────────────────────────────────────────────────────
class salesItemsInline(TabularInline):
    model = salesItems
    extra = 0
    readonly_fields = ("product_id", "price", "qty", "total")
    fields = ("product_id", "price", "qty", "total")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ─────────────────────────────────────────────────────────
#  MEREK & KATEGORI
# ─────────────────────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display   = ("preview_image", "name", "description_short", "status_badge", "date_added")
    list_display_links = ("name",)
    list_filter    = ("status",)
    search_fields  = ("name",)
    ordering       = ("name",)
    inlines        = [CategoryTypeInline]

    fieldsets = (
        ("Informasi Merek", {"fields": ("name", "description", "image")}),
        ("Status", {"fields": ("status",)}),
    )

    @admin.display(description="Foto")
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:80px;height:45px;object-fit:cover;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">',
                obj.image.url,
            )
        return format_html('<span style="color:#9ca3af;">{}</span>', '—')

    @admin.display(description="Deskripsi")
    def description_short(self, obj):
        return obj.description[:60] + "…" if len(obj.description) > 60 else obj.description

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.status == 1:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;padding:2px 10px;'
                'border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Aktif'
            )
        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;padding:2px 10px;'
            'border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Nonaktif'
        )


# ─────────────────────────────────────────────────────────
#  TIPE MEREK (standalone)
# ─────────────────────────────────────────────────────────
@admin.register(CategoryType)
class CategoryTypeAdmin(ModelAdmin):
    list_display  = ("name", "category")
    list_filter   = ("category",)
    search_fields = ("name", "category__name")
    ordering      = ("category", "name")


# ─────────────────────────────────────────────────────────
#  PRODUK
# ─────────────────────────────────────────────────────────
@admin.register(Products)
class ProductsAdmin(ModelAdmin):
    list_display   = (
        "preview_image", "code", "name", "category_id",
        "formatted_price", "stock_badge", "warranty_badge", "status_badge",
    )
    list_display_links = ("code", "name")
    list_filter    = ("status", "category_id")
    search_fields  = ("code", "name", "description")
    ordering       = ("category_id", "name")
    list_per_page  = 20

    fieldsets = (
        ("Identitas Produk", {
            "fields": ("code", "name", "category_id", "description"),
        }),
        ("Harga & Stok", {
            "fields": ("price", "hpp", "stock", "warranty"),
        }),
        ("Media & Status", {
            "fields": ("image", "status"),
        }),
    )

    @admin.display(description="Foto")
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:42px;height:42px;object-fit:cover;border-radius:8px;">',
                obj.image.url,
            )
        return format_html('<span style="color:#9ca3af;">{}</span>', '—')

    @admin.display(description="Harga", ordering="price")
    def formatted_price(self, obj):
        return "Rp {:,.0f}".format(obj.price).replace(",", ".")

    @admin.display(description="Stok", ordering="stock")
    def stock_badge(self, obj):
        stok = obj.stock or 0
        if stok > 10:
            color = "#dcfce7"; text_color = "#166534"
        elif stok > 0:
            color = "#fef9c3"; text_color = "#854d0e"
        else:
            color = "#fee2e2"; text_color = "#991b1b"
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>',
            color, text_color, stok,
        )

    @admin.display(description="Garansi")
    def warranty_badge(self, obj):
        hari = obj.warranty or 0
        if hari > 0:
            return format_html(
                '<span style="background:#eff6ff;color:#1e40af;padding:2px 10px;'
                'border-radius:20px;font-size:0.75rem;font-weight:600;">{} Hari</span>', hari
            )
        return format_html('<span style="color:#9ca3af;font-size:0.75rem;">{}</span>', 'Non-Garansi')

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.status == 1:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;padding:2px 10px;'
                'border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Aktif'
            )
        return format_html(
            '<span style="background:#f3f4f6;color:#6b7280;padding:2px 10px;'
            'border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Arsip'
        )


# ─────────────────────────────────────────────────────────
#  PENJUALAN
# ─────────────────────────────────────────────────────────
@admin.register(Sales)
class SalesAdmin(ModelAdmin):
    list_display   = (
        "code", "formatted_grand_total", "payment_badge",
        "customer_info", "discount_info", "date_added",
    )
    list_display_links = ("code",)
    list_filter    = ("payment_method", "date_added")
    search_fields  = ("code", "customer_name", "customer_wa")
    ordering       = ("-date_added",)
    readonly_fields = (
        "code", "sub_total", "grand_total", "diskon_amount", "diskon",
        "tendered_amount", "amount_change", "date_added", "date_updated",
    )
    inlines        = [salesItemsInline]
    list_per_page  = 25
    date_hierarchy = "date_added"

    fieldsets = (
        ("Info Transaksi", {
            "fields": ("code", "date_added", "payment_method"),
        }),
        ("Rincian Pembayaran", {
            "fields": (
                "sub_total", "diskon", "diskon_amount",
                "grand_total", "tendered_amount", "amount_change",
            ),
        }),
        ("Data Pelanggan", {
            "fields": ("customer_name", "customer_wa", "customer_address"),
        }),
    )

    @admin.display(description="Total Akhir", ordering="grand_total")
    def formatted_grand_total(self, obj):
        formatted_val = "{:,.0f}".format(obj.grand_total).replace(",", ".")
        return format_html(
            '<span style="font-weight:700;color:#166534;">Rp {}</span>', formatted_val
        )

    @admin.display(description="Metode Bayar")
    def payment_badge(self, obj):
        method = obj.payment_method or "Tunai"
        colors = {
            "Tunai":    ("#dcfce7", "#166534"),
            "QRIS":     ("#eff6ff", "#1e40af"),
            "Transfer": ("#fef3c7", "#92400e"),
        }
        bg, fg = colors.get(method, ("#f3f4f6", "#374151"))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>',
            bg, fg, method,
        )

    @admin.display(description="Pelanggan")
    def customer_info(self, obj):
        if obj.customer_name:
            return format_html(
                '<span style="font-weight:600;">{}</span>'
                '<br><span style="color:#6b7280;font-size:0.75rem;">{}</span>',
                obj.customer_name,
                obj.customer_wa or "—",
            )
        return format_html('<span style="color:#9ca3af;">{}</span>', 'Umum')

    @admin.display(description="Diskon")
    def discount_info(self, obj):
        if obj.diskon and obj.diskon > 0:
            formatted_amount = "{:,.0f}".format(obj.diskon_amount).replace(",", ".")
            return format_html(
                '<span style="color:#dc2626;font-weight:600;">{}%</span>'
                '<br><span style="color:#6b7280;font-size:0.75rem;">Rp {}</span>',
                int(obj.diskon),
                formatted_amount
            )
        return format_html('<span style="color:#9ca3af;">{}</span>', '—')


    @admin.display(description="Total Akhir", ordering="grand_total")
    def formatted_grand_total(self, obj):
        formatted_val = "{:,.0f}".format(obj.grand_total).replace(",", ".")
        return format_html(
            '<span style="font-weight:700;color:#166534;">Rp {}</span>', formatted_val
        )

# ─────────────────────────────────────────────────────────
#  SUPPLIER
# ─────────────────────────────────────────────────────────
@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    list_display = ("name", "status_badge", "date_added")
    list_filter = ("status",)
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.status == 1:
            return format_html('<span style="background:#dcfce7;color:#166534;padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Aktif')
        return format_html('<span style="background:#fee2e2;color:#991b1b;padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Nonaktif')

# ─────────────────────────────────────────────────────────
#  INLINE: Item Barang Masuk
# ─────────────────────────────────────────────────────────
class purchaseItemsInline(TabularInline):
    model = purchaseItems
    extra = 0
    readonly_fields = ("product_id", "price", "qty", "total")
    fields = ("product_id", "price", "qty", "total")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

# ─────────────────────────────────────────────────────────
#  BARANG MASUK (PURCHASES)
# ─────────────────────────────────────────────────────────
@admin.register(Purchases)
class PurchasesAdmin(ModelAdmin):
    list_display = ("code", "supplier_id", "formatted_grand_total", "date_added")
    list_filter = ("date_added", "supplier_id")
    search_fields = ("code", "supplier_id__name")
    ordering = ("-date_added",)
    readonly_fields = ("code", "supplier_id", "grand_total", "date_added", "date_updated")
    inlines = [purchaseItemsInline]
    date_hierarchy = "date_added"

    @admin.display(description="Total Akhir", ordering="grand_total")
    def formatted_grand_total(self, obj):
        formatted_val = "{:,.0f}".format(obj.grand_total).replace(",", ".")
        return format_html('<span style="font-weight:700;color:#166534;">Rp {}</span>', formatted_val)

# ─────────────────────────────────────────────────────────
#  KLAIM GARANSI
# ─────────────────────────────────────────────────────────
@admin.register(WarrantyClaim)
class WarrantyClaimAdmin(ModelAdmin):
    list_display = ("sale_id", "product_id", "status_badge", "formatted_cost", "date_added")
    list_filter = ("status", "date_added")
    search_fields = ("sale_id__code", "product_id__name", "description")
    ordering = ("-date_added",)
    readonly_fields = ("date_added", "date_updated")

    fieldsets = (
        ("Informasi Klaim", {
            "fields": ("sale_id", "product_id", "description")
        }),
        ("Penyelesaian", {
            "fields": ("cost", "status")
        }),
        ("Sistem", {
            "fields": ("date_added", "date_updated"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Biaya", ordering="cost")
    def formatted_cost(self, obj):
        formatted_val = "{:,.0f}".format(obj.cost).replace(",", ".")
        return format_html('<span style="font-weight:700;color:#991b1b;">Rp {}</span>', formatted_val)

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.status == 1:
            return format_html('<span style="background:#dcfce7;color:#166534;padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Selesai')
        return format_html('<span style="background:#fef3c7;color:#92400e;padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">{}</span>', 'Proses Servis')

# ─────────────────────────────────────────────────────────
#  RETUR BARANG
# ─────────────────────────────────────────────────────────
@admin.register(Returns)
class ReturnsAdmin(ModelAdmin):
    list_display = ("product_id", "supplier_id", "type", "qty", "date_added")
    list_filter = ("type", "date_added")
    search_fields = ("product_id__name", "supplier_id__name", "reason")
    ordering = ("-date_added",)
    readonly_fields = ("date_added", "date_updated")

    fieldsets = (
        ("Informasi Retur", {
            "fields": ("product_id", "supplier_id", "type", "qty", "reason")
        }),
        ("Sistem", {
            "fields": ("date_added", "date_updated"),
            "classes": ("collapse",)
        }),
    )

