import requests
from lxml import html
from urllib.parse import urlencode
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def consultar_rnc_cedula(self, vat):
        _logger.info('ConsultaDGII')
        
        URL_CONSULTA_CIUDADANOS = "https://www.dgii.gov.do/app/WebApps/ConsultasWeb/consultas/rnc.aspx"

        def _load_page(url):
            response = requests.get(url)
            response.raise_for_status()
            return html.fromstring(response.content)

        def _post_back(url, data, cookies):
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            response = requests.post(url, data=urlencode(data), cookies=cookies, headers=headers)
            response.raise_for_status()
            return html.fromstring(response.content)

        def get_xpath_value(page, xpath):
            values = page.xpath(xpath)
            return values[0].strip() if values else ""

        session = requests.Session()
        page = _load_page(URL_CONSULTA_CIUDADANOS)

        viewstate = get_xpath_value(page, "//input[@id='__VIEWSTATE']/@value")
        eventvalidation = get_xpath_value(page, "//input[@name='__EVENTVALIDATION']/@value")
        viewstategenerator = get_xpath_value(page, "//input[@name='__VIEWSTATEGENERATOR']/@value")

        form_data = {
            "ctl00$smMain": "ctl00$cphMain$upBusqueda|ctl00$cphMain$btnBuscarPorRNC",
            "ctl00$cphMain$txtRNCCedula": vat,
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "__ASYNCPOST": "true",
            "ctl00$cphMain$btnBuscarPorRNC": "Buscar"
        }

        result_page = _post_back(URL_CONSULTA_CIUDADANOS, form_data, session.cookies)

        result = {
            "estado": get_xpath_value(result_page, "//table[@id='ctl00_cphMain_dvDatosContribuyentes']//tr[6]/td[2]/text()"),
        }

        _logger.info("Resultado de consulta DGII para VAT %s: %s", vat, result["estado"])

        return result if result["estado"] == "ACTIVO" else False

    @api.model
    def action_consultar_dgii(self):
        for record in self:
            if record.vat:
                result = self.consultar_rnc_cedula(record.vat)

                if not result:
                    raise ValidationError("El cliente está inhabilitado o no se encuentra en la DGII.")
                else:
                    raise ValidationError("El cliente está activo en la DGII.")
            else:
                raise ValidationError("El campo RNC/Cédula (vat) está vacío. Por favor, complete el campo antes de consultar.")
