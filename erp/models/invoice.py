from accounting.models import Account, Transaction
from common.validators import date_is_present_or_past
from contact.models import Contact
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from persons.models import Company, PhysicalAddress


class FiscalPosition(models.Model):
    """
    A fiscal position is a classification given by a government to an
    individual or a company, which categorizes them into a tax-paying class.
    """

    name = models.CharField(_("name"), max_length=50, unique=True)
    code = models.SlugField(
        _("code"),
        max_length=15,
        default="",
        blank=True,
        help_text=_("Some local official electronic systems handle " "specific codes."),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("fiscal position")
        verbose_name_plural = _("fiscal positions")
        default_permissions = ("view", "add", "change", "delete")


class CompanyInvoice(models.Model):
    """
    You need to define at least one to start invoicing, but you can add
    as many as you need.
    This is an extension of 'persons.models.Company'.
    """

    persons_company = models.OneToOneField(
        Company, verbose_name=_("company"), on_delete=models.CASCADE
    )
    legal_name = models.CharField(_("legal name"), max_length=300)
    initiated_activities = models.DateField(
        _("initiated activities"),
        blank=True,
        null=True,
        validators=[date_is_present_or_past],
    )
    fiscal_position = models.ForeignKey(
        FiscalPosition,
        verbose_name=_("fiscal position"),
        related_name="companies",
        related_query_name="company",
        on_delete=models.PROTECT,
        db_index=False,
        blank=True,
        null=True,
        help_text=_(
            "Certain countries require a fiscal position for " "its taxpayers."
        ),
    )
    fiscal_address = models.ForeignKey(
        PhysicalAddress,
        verbose_name=_("fiscal address"),
        related_name="+",
        related_query_name="+",
        on_delete=models.CASCADE,
        db_index=False,
        blank=True,
        null=True,
    )
    default_invoice_debit_account = models.ForeignKey(
        Account,
        verbose_name=_("default invoice debit account"),
        related_name="+",
        related_query_name="+",
        on_delete=models.PROTECT,
        db_index=False,
        null=True,
        blank=True,
    )
    default_invoice_credit_account = models.ForeignKey(
        Account,
        verbose_name=_("default invoice credit account"),
        related_name="+",
        related_query_name="+",
        on_delete=models.PROTECT,
        db_index=False,
        null=True,
        blank=True,
    )

    def __str__(self):
        return str(self.persons_company)

    class Meta:
        verbose_name = _("company")
        verbose_name_plural = _("companies")
        default_permissions = ("view", "add", "change", "delete")


class ContactInvoice(models.Model):
    """
    Contact extension by Invoice.
    """

    contact_contact = models.OneToOneField(
        Contact, verbose_name=_("contact"), on_delete=models.CASCADE
    )
    legal_name = models.CharField(_("legal name"), max_length=300)
    fiscal_position = models.ForeignKey(
        FiscalPosition,
        verbose_name=_("fiscal position"),
        related_name="contacts",
        related_query_name="contact",
        on_delete=models.PROTECT,
        db_index=False,
        help_text=_(
            "Certain countries require a fiscal position for " "its taxpayers."
        ),
    )
    fiscal_address = models.ForeignKey(
        PhysicalAddress,
        verbose_name=_("fiscal address"),
        related_name="+",
        related_query_name="+",
        on_delete=models.CASCADE,
        db_index=False,
    )

    def __str__(self):
        return str(self.contact_contact)

    class Meta:
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")
        default_permissions = ("view", "add", "change", "delete")


class VAT(models.Model):
    """
    VAT is a type of tax to consumption. Every country has it.
    """

    name = models.CharField(
        _("name"), max_length=15, unique=True, help_text=_("i.e. 8% US")
    )
    code = models.SlugField(
        _("code"),
        max_length=15,
        default="",
        blank=True,
        help_text=_("Some local official electronic systems handle " "specific codes."),
    )
    tax = models.DecimalField(
        _("tax"),
        max_digits=5,
        decimal_places=2,
        help_text=_("A value between 0.00 and 1.00"),
        validators=[MinValueValidator(0.00), MaxValueValidator(1.00)],
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("VAT")
        verbose_name_plural = _("VATs")
        default_permissions = ("view", "add", "change", "delete")


class Product(models.Model):
    """
    A basic product. It could also be a service.
    See other modules like 'sales' for more advanced products.
    """

    invoice_company = models.ForeignKey(
        CompanyInvoice,
        verbose_name=_("company"),
        related_name="products",
        related_query_name="product",
        on_delete=models.PROTECT,
        db_index=True,
    )
    name = models.CharField(
        _("name"),
        max_length=150,
        help_text=_("It could also be a service."),
        db_index=True,
    )
    current_price = models.DecimalField(
        _("current price"),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.00)],
    )
    vat = models.ForeignKey(
        VAT,
        verbose_name=_("VAT"),
        related_name="products",
        related_query_name="product",
        on_delete=models.PROTECT,
        db_index=True,
    )

    def __str__(self):
        return "%(name)s" % {"name": self.name}

    class Meta:
        unique_together = ("invoice_company", "name")
        verbose_name = _("product")
        verbose_name_plural = _("products")
        default_permissions = ("view", "add", "change", "delete")


class InvoiceLine(models.Model):
    """
    An invoice is composed of lines or entries, which have a product,
    a price and a quantity.
    """

    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        Product,
        verbose_name=_("product"),
        related_name="invoice_lines",
        related_query_name="invoice_line",
        on_delete=models.PROTECT,
        db_index=False,
    )
    price_sold = models.DecimalField(
        _("price sold"),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.00)],
    )
    discount = models.DecimalField(
        _("discount"),
        max_digits=5,
        decimal_places=2,
        default=0.00,
        blank=True,
        help_text=_("A number between 0.00 and 1.00"),
        validators=[MinValueValidator(0.00), MaxValueValidator(1.00)],
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    description = models.CharField(
        _("description"), max_length=300, default="", blank=True
    )

    def __str__(self):
        return "%(product)s x %(quantity)s" % {
            "product": self.product,
            "quantity": self.quantity,
        }

    class Meta:
        verbose_name = _("invoice line")
        verbose_name_plural = _("invoice lines")
        default_permissions = ("view", "add", "change", "delete")


INVOICETYPE_CLASS_BILL = "B"
INVOICETYPE_CLASS_DEBIT = "D"
INVOICETYPE_CLASS_CREDIT = "C"
INVOICETYPE_CLASSES = (
    (INVOICETYPE_CLASS_BILL, _("Bill")),
    (INVOICETYPE_CLASS_DEBIT, _("Debit")),
    (INVOICETYPE_CLASS_CREDIT, _("Credit")),
)


class InvoiceType(models.Model):
    """
    Government defined invoice types.
    """

    name = models.CharField(_("name"), max_length=150)
    invoice_type_class = models.CharField(
        _("invoice type class"), max_length=1, choices=INVOICETYPE_CLASSES
    )
    code = models.SlugField(
        _("code"),
        max_length=15,
        default="",
        blank=True,
        help_text=_("Some local official electronic systems handle " "specific codes."),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("invoice type")
        verbose_name_plural = _("invoice types")
        default_permissions = ("view", "add", "change", "delete")


INVOICE_STATUSTYPE_DRAFT = "D"
INVOICE_STATUSTYPE_ACCEPTED = "A"
INVOICE_STATUSTYPE_AUTHORIZED = "T"
INVOICE_STATUSTYPE_CANCELED = "C"
INVOICE_STATUS_TYPES = (
    (INVOICE_STATUSTYPE_DRAFT, _("Draft")),
    (INVOICE_STATUSTYPE_ACCEPTED, _("Accepted")),
    (INVOICE_STATUSTYPE_AUTHORIZED, _("Authorized")),
    (INVOICE_STATUSTYPE_CANCELED, _("Canceled")),
)


class Invoice(models.Model):
    """
    The invoices themselves.
    """

    id = models.AutoField(primary_key=True)
    invoice_company = models.ForeignKey(
        CompanyInvoice,
        verbose_name=_("company"),
        related_name="invoices",
        related_query_name="invoice",
        on_delete=models.PROTECT,
        db_index=True,
    )
    invoice_contact = models.ForeignKey(
        ContactInvoice,
        verbose_name=_("contact"),
        related_name="invoices",
        related_query_name="invoice",
        on_delete=models.PROTECT,
        db_index=True,
    )
    related_invoice = models.ForeignKey(
        "self",
        verbose_name=_("related invoice"),
        related_name="+",
        related_query_name="+",
        on_delete=models.PROTECT,
        db_index=False,
        blank=True,
        null=True,
    )
    number = models.BigIntegerField(_("number"), default=0, blank=True)
    invoice_lines = models.ManyToManyField(
        InvoiceLine,
        verbose_name=_("invoice lines"),
        related_name="+",
        related_query_name="invoice",
        blank=True,
    )
    invoice_type = models.ForeignKey(
        InvoiceType,
        verbose_name=_("invoice type"),
        related_name="invoices",
        related_query_name="invoice",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    invoice_date = models.DateField(
        _("date"),
        help_text=_("Not necessarily today."),
        validators=[date_is_present_or_past],
    )
    status = models.CharField(
        _("status"),
        max_length=1,
        choices=INVOICE_STATUS_TYPES,
        default=INVOICE_STATUSTYPE_DRAFT,
    )
    subtotal = models.DecimalField(
        _("subtotal"),
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_("Total without taxes."),
    )
    total = models.DecimalField(
        _("total"),
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_("Subtotal plus taxes."),
    )
    notes = models.TextField(_("notes"), blank=True, default="")
    transaction = models.ForeignKey(
        Transaction,
        verbose_name=_("transaction"),
        related_name="+",
        related_query_name="invoice",
        on_delete=models.PROTECT,
        db_index=False,
        blank=True,
        null=True,
    )

    def __str__(self):
        return "%(invoice_company)s : %(number)s" % {
            "invoice_company": str(self.invoice_company),
            "number": str(self.number),
        }

    class Meta:
        verbose_name = _("invoice")
        verbose_name_plural = _("invoices")
        default_permissions = ("view", "add", "change", "delete")


class FiscalPositionHasInvoiceTypeAllowed(models.Model):
    """
    In some countries, Fiscal Positions are allowed to use certain Invoice
    Types.
    """

    fiscal_position_issuer = models.ForeignKey(
        FiscalPosition,
        verbose_name=_("fiscal position issuer"),
        related_name="+",
        related_query_name="+",
        on_delete=models.PROTECT,
        db_index=True,
    )
    invoice_type = models.ForeignKey(
        InvoiceType,
        verbose_name=_("invoice type"),
        related_name="+",
        related_query_name="+",
        on_delete=models.PROTECT,
        db_index=True,
    )
    fiscal_position_receiver = models.ForeignKey(
        FiscalPosition,
        verbose_name=_("fiscal position receiver"),
        related_name="+",
        related_query_name="+",
        on_delete=models.PROTECT,
        db_index=True,
    )

    def __str__(self):
        return (
            str(self.fiscal_position_issuer)
            + "->"
            + (str(self.invoice_type) + "->" + (str(self.fiscal_position_receiver)))
        )

    class Meta:
        verbose_name = _("fiscal position has invoice type allowed")
        verbose_name_plural = _("fiscal positions have invoice types allowed")
        default_permissions = ("view", "add", "change", "delete")
