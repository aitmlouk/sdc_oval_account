# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons import decimal_precision as dp

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
    
class ResCompany(models.Model):
    _inherit = 'res.company' 
    
    idf = fields.Char(string='Identifiant Fiscal')
    rc = fields.Char(string='Registre du commerce')
    tc = fields.Char(string='Tribunal de commerce')
    itp = fields.Char(string='Patente')
    ice = fields.Char(string='I.C.E')
    cnss = fields.Char(string='CNSS')  
    idfp = fields.Char(string='Identifiant Taxe Professionnelle')
    drp = fields.Char(string='Direction régionale ou préfectorale')
    subdivision = fields.Char(string='Subdivision')
    code_dr = fields.Char(string='Code DR ou DP')
    
    company_type_id = fields.Many2one('res.company.type',string='Type de société')
    capital = fields.Float(string='Capital')
    tele = fields.Char(string='Télécopie')
    date = fields.Date(string='Date inscription')
    
    
    regim_tva = fields.Selection([('1', 'Déclaration mensuelle'), ('2', 'Déclaration trimestrielle')], string= 'Régime T.V.A')
    fait_tva = fields.Selection([('1', 'Encaissement'), ('2', 'Débit')], string= 'Fait générateur TVA')
    
    recette = fields.Char(string='Recette')
    code_recette = fields.Char(string='Code recette')
    raison_s = fields.Char(string='Raison sociale') 
    fj = fields.Char(string='Forme juridique')
    adresse_siege = fields.Char(string='Adresse du siège')
    city_id = fields.Char(string='Ville du siège')
    
    type_lf = fields.Many2one('type.liasse', string= 'Type de liasse fiscale')
    invoice_description = fields.Char(string='Description factures vente par défaut')

class ResCompanyType(models.Model):
    _name = 'res.company.type' 
    
    name = fields.Char(string='Nom')
    code = fields.Char(string='Code')
    
class TypLiasee(models.Model):
    _name = 'type.liasse'
    
    name=fields.Char(string='Libellé du modèle')
    identifiant=fields.Char(string='Identifiant du modèle')
    type=fields.Char(string='Type de liasse fiscale')
      
    
class Partner(models.Model):
    _inherit = 'res.partner' 
       
    rc = fields.Char(string='Registre du commerce')
    tc = fields.Char(string='Tribunal de commerce')
    ifs = fields.Char(string='Identifiant Fiscal')
    cnss = fields.Char(string='C.N.S.S.')
    patente = fields.Char(string='Patente')
    ice = fields.Char(string='I.C.E')
    description_facture = fields.Char(string='Description facture')
    activite_id = fields.Many2one('partner.activity',string='Activités')
    supplier_account = fields.Char(string='Ancien compte fournisseur')
    
class PartnerActivity(models.Model):
    _name = 'partner.activity' 
    
    name = fields.Char(string='Nom')
    code = fields.Char(string='Code')
    
class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    description_facture = fields.Char(string='Description facture', related='company_id.invoice_description', readonly=True)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    description_facture = fields.Char(string='Description facture', related='company_id.invoice_description', readonly=True)
        
class PaymentMode(models.Model):
    _name = 'payment.mode'
     
    name=fields.Char(string='Mode de paiement', required=True)
    supplier_def=fields.Boolean(string='Par défaut règlements fournisseurs')
    prohibit=fields.Boolean(string='Interdire')
 
class AccountPayment(models.Model):
    _inherit = "account.payment"
    payment_mode = fields.Many2one('payment.mode',string='Mode de paiement')
    deadline = fields.Date(string='Échéance')
    number = fields.Char(string='Pièce N°')
    
class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = "hr.expense.sheet.register.payment.wizard"
    payment_mode = fields.Many2one('payment.mode',string='Mode de paiement')
    number = fields.Char(string='Pièce N°')
       
    def _get_payment_vals(self):
        """ Hook for extension """
        return {
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'payment_mode': self.payment_mode.id,
            'number': self.number
        }       
        
        
class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"
    
    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        '''
        amount = self._compute_payment_amount(invoices) if self.multi else self.amount
        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'payment_mode': self.payment_mode.id,
            'deadline': self.deadline,
            'number': self.number
        }
        

class AccountTax(models.Model):
    _inherit = 'account.tax'   
    code_dgi=fields.Char(string='Code DGI', required=True)
    teype_vent=fields.Char(string='Type ventilation', required=True)
    type_tva=fields.Char(string='Type TVA')
    impact_tva=fields.Char(string='Impact déclaration TVA')

class ProductTemplate(models.Model):
    _inherit = 'product.template'   
    #teype_vent=fields.Char(string='Ventilation')
    teype_vent = fields.Char(compute='_get_code',string='Ventilation', readonly=True, store=True)
    teype_vent_sale = fields.Char(compute='_get_type_ventsal',string='Ventilation', readonly=True, store=True)
    
    @api.multi
    @api.depends('supplier_taxes_id')
    def _get_code(self):
        data =[]
        if self.supplier_taxes_id:      
            for t in self.supplier_taxes_id:
                data.append(str(t.code_dgi)+'-'+str(t.teype_vent))
            self.teype_vent = (', '.join(map(str, data)))
        else:pass
    
    @api.multi
    @api.depends('taxes_id')
    def _get_type_ventsal(self):
        data =[]
        if self.taxes_id:    
            for t in self.taxes_id:
                data.append(str(t.code_dgi)+'-'+str(t.teype_vent))
            self.teype_vent_sale = (', '.join(map(str, data))) 
        else:pass
            
class ProductProduct(models.Model):
    _inherit = 'product.product'   
    #teype_vent=fields.Char(string='Ventilation')
    teype_vent = fields.Char(compute='_get_code_dgi',string='Ventilation', readonly=True, store=True)
    
    
    
    @api.multi
    @api.depends('supplier_taxes_id')
    def _get_code_dgi(self):  
        data =[]
        for t in self.supplier_taxes_id:
            data.append(str(t.code_dgi)+'-'+str(t.teype_vent))
        self.teype_vent = (', '.join(map(str, data)))
    
        return True 
          
class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'   
    
    tva_amount = fields.Float(compute='_get_tva',string='TVA', readonly=True, store=True)
    
    
    
    @api.multi
    @api.depends('move_line_ids')
    def _get_tva(self):  
        data =[]
        for t in self.move_line_ids:
            print('------move_line_ids---------')
            print(t)
            print(t.name)
            print('------------------------------')  
        return True    
    