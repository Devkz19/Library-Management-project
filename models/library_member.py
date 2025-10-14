from odoo import models, fields, api
from datetime import date

class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Library Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    membership_id = fields.Char(
    string='Membership ID',
    readonly=True,
    copy=False,
    default='New',
    tracking=True
    )
    
    first_name = fields.Char(required=True, tracking=True)
    middle_name = fields.Char(tracking=True)
    last_name = fields.Char(required=True, tracking=True)
    issue_ids = fields.One2many('library.issue', 'member_id', string="Issues")
    dob = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=True)

    name = fields.Char(compute="_compute_name", store=True)

    email = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    date_joined = fields.Date(default=fields.Date.today, tracking=True)

    membership_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ], default='active', tracking=True)

    user_type = fields.Selection([
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('general', 'General Member'),
    ], tracking=True)

    street = fields.Char(tracking=True)
    city = fields.Char(tracking=True)
    state0 = fields.Char(tracking=True)
    zip_code = fields.Char(tracking=True)
    photo = fields.Binary(string="Photo")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', tracking=True)

    # Button actions
    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'

    @api.depends('first_name', 'middle_name', 'last_name')
    def _compute_name(self):
        for rec in self:
            parts = filter(None, [rec.first_name, rec.middle_name, rec.last_name])
            rec.name = " ".join(parts)
            
    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                today = date.today()
                record.age = today.year - record.dob.year - \
                             ((today.month, today.day) < (record.dob.month, record.dob.day))
            else:
                record.age = 0        
    
    @api.model
    def create(self, vals):
        if vals.get('membership_id', 'New') == 'New':
            vals['membership_id'] = self.env['ir.sequence'].next_by_code('library.member') or '/'
        return super(LibraryMember, self).create(vals)

    def print_issued_books_report(self):
        return self.env.ref('library_management.action_report_member_issued_books').report_action(self)
    
    def action_send_welcome_email(self):
        template = self.env.ref('library_management.mail_template_library_member_welcome')
        for member in self:
            if member.email:
                template.send_mail(member.id, force_send=True)


class ChangeStateWizard(models.TransientModel):
    _name = 'library.change.state.wizard'
    _description = 'Change State Wizard'

    new_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ], string="New State", required=True)

    def action_change_state(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            record = self.env['library.member'].browse(active_id)
            record.state = self.new_state
