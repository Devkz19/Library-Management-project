from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo.exceptions import UserError


class LibraryIssue(models.Model):
    _name = 'library.issue'
    _description = 'Issued Book'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    book_id = fields.Many2one('library.book', string="Book", required=True, tracking=True)
    signature = fields.Binary("Member Signature")
    member_id = fields.Many2one('library.member', string="Member", required=True, tracking=True)
    member_email = fields.Char(related='member_id.email')
    issue_date = fields.Date(string="Issue Date", default=fields.Date.today, tracking=True)
    return_date = fields.Date(string="Return Date", tracking=True)
    
    issue_type = fields.Selection([
        ('issue', 'Issue'),
        ('purchase', 'Purchase'),
    ], string="Request Type", default='issue', required=True, tracking=True)

    issue_price = fields.Float(string="Issue Price", related='book_id.issue_price', readonly=True)
    purchase_price = fields.Float(string="Purchase Price", related='book_id.purchase_price', readonly=True)


    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ], string="Payment Status", default='unpaid', tracking=True)

    payment_date = fields.Date(string="Payment Date")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('returned', 'Returned')
    ], string="Status", default='draft', tracking=True)
    
    actual_return_date = fields.Date(string="Actual Return Date")
    penalty = fields.Float(string="Penalty")

    price_to_pay = fields.Float(string="Price to Pay", compute="_compute_price_to_pay", store=True)
    
    @api.constrains('issue_date', 'return_date')
    def _check_dates(self):
        for record in self:
            if record.return_date and record.issue_date > record.return_date:
                raise ValidationError("The return date cannot be before the issue date.")
            
    @api.onchange('member_id')
    def _onchange_member_id(self):
        if self.member_id:
            self.member_email = self.member_id.email
        else:
            self.member_email = False        

    @api.depends('issue_type', 'book_id')
    def _compute_price_to_pay(self):
        for rec in self:
            if rec.issue_type == 'purchase':
                rec.price_to_pay = rec.book_id.purchase_price
            else:
                rec.price_to_pay = rec.book_id.issue_price

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_book_available_copies()
        for rec in records:
            rec.message_post(body=f"{rec.issue_type.capitalize()} request created for book '{rec.book_id.name}'.")
        return records

    def write(self, vals):
        res = super().write(vals)
        self._update_book_available_copies()
        return res

    def unlink(self):
        books = self.mapped('book_id')
        res = super().unlink()
        books._compute_available_copies()
        return res

    def _update_book_available_copies(self):
        for rec in self:
            if rec.book_id:
                rec.book_id._compute_available_copies()

    def action_confirm(self):
        for rec in self:
            if rec.issue_type == 'issue' and rec.return_date:
                max_return = rec.issue_date + timedelta(days=14)
                if rec.return_date > max_return:
                    raise ValidationError("Return date cannot exceed 2 weeks for issued books.")
            # For 'purchase' type, reduce num_copies when confirmed
            if rec.issue_type == 'purchase':
                # Check if there are enough copies before confirming
                if rec.book_id.num_copies <= 0:
                    raise UserError(_("No copies available for purchase of this book."))
                rec.book_id.num_copies -= 1  # reduce total stock
            
            rec.state = 'confirmed'
            rec.message_post(body=f"{rec.issue_type.capitalize()} confirmed for '{rec.book_id.name}'.")
            # Recalculate available copies after confirmation
            rec.book_id._compute_available_copies()  
            
    def action_send_issue_email(self):
        self.ensure_one() # Ensures the method is called on a single record
        template = self.env.ref('library_management.mail_template_library_book_issue', raise_if_not_found=False)
        if not template:
            raise UserError(_("Email template not found! Please check the XML ID or update the module."))
        template.send_mail(self.id, force_send=True)

    def action_return(self):
        for rec in self:
            if rec.issue_type == 'issue': # Only for 'issue' type
                rec.state = 'returned'
                rec.return_date = fields.Date.today()
                rec.message_post(body=f"Book '{rec.book_id.name}' returned by {rec.member_id.name}.")
                rec.book_id._compute_available_copies() # Recalculate available copies after return
            else: # If it's a 'purchase', it doesn't get "returned"
                raise UserError(_("Only 'Issue' type records can be returned."))
    
    @api.depends('book_id', 'member_id', 'issue_type', 'issue_date')
    def _compute_display_name(self):
        for record in self:
            if record.book_id and record.member_id:
                base_name = f"{record.book_id.name} - {record.member_id.name}"
                # Uncomment next line if you want to optionally show additional info
                # base_name += f" ({record.issue_type}, {record.issue_date})"
                record.display_name = base_name
            else:
                record.display_name = "New Issue"
