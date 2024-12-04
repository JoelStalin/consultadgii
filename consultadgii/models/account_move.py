from odoo import models, api
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def action_post(self):
        for move in self:
            if move.partner_id.vat:  # Verifica si el cliente tiene un RNC/Cédula
                result = move.partner_id.consultar_rnc_cedula(move.partner_id.vat)
                if not result or result.get("estado") != "ACTIVO":  # Verifica si el cliente no está activo
                    raise ValidationError("El cliente está inhabilitado o no se encuentra en la DGII.")
            else:
                raise ValidationError("El cliente no tiene un RNC/Cédula asociado.")

        # Llamada al método original para completar el proceso de posting
        return super(AccountMove, self).action_post()
