from odoo import models


class ReportCortenLabel(models.AbstractModel):
    _name = "report.corten_label_magnet.report_label"
    _description = "Magnet label report"

    def _get_report_values(self, docids, data):
        """Resolve the records to label and the copies of each.

        The product label wizard calls the report with no docids and a
        `quantity_by_product` map; the location action calls it with docids.
        """
        data = data or {}
        quantities = data.get("quantity_by_product") or {}
        active_model = data.get("active_model")

        if active_model in ("product.template", "product.product") and quantities:
            ids = [int(p) for p in quantities]
            docs = self.env[active_model].browse(ids).exists()
            copies = {int(p): max(int(q), 1) for p, q in quantities.items()}
        else:
            docs = self.env["stock.location"].browse(docids or []).exists()
            copies = {rec.id: 1 for rec in docs}

        return {"docs": docs, "copies": copies}
