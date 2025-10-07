from odoo import models, fields, api
from datetime import date

class LibraryIssueReturnWizard(models.TransientModel):
    _name = 'library.issue.return.wizard'
    _description = 'Return Book Wizard'

    issue_id = fields.Many2one('library.issue', string="Issued Record", required=True)
    issue_date = fields.Date(related='issue_id.issue_date', string="Issue Date", store=False, readonly=True)

    return_date = fields.Date(
        string="Return Date",
        default=fields.Date.context_today,
        required=True,
       
    )

    extra_days = fields.Integer(
        string="Extra Days",
        compute="_compute_penalty",
        store=False,
        tracking=True
    )

    penalty_amount = fields.Float(
        string="Penalty Amount",
        compute="_compute_penalty",
        store=False,
        tracking=True
    )

    penalty_per_day = fields.Float(string="Penalty Rate Per Day", default=10.0)

    @api.depends('return_date', 'issue_id.return_date')
    def _compute_penalty(self):
        for wizard in self:
            if wizard.issue_id.return_date and wizard.return_date:
                delta = (wizard.return_date - wizard.issue_id.return_date).days
                wizard.extra_days = max(0, delta)
                wizard.penalty_amount = wizard.extra_days * wizard.penalty_per_day
            else:
                wizard.extra_days = 0
                wizard.penalty_amount = 0.0
    
    def confirm_return(self):
        self.ensure_one()

        # Write updates to the issue record
        self.issue_id.write({
            'actual_return_date': self.return_date,
            'penalty': self.penalty_amount,
            'state': 'returned',
        })

        # Post a message to the chatter
        msg = f" Book returned on {self.return_date.strftime('%d-%m-%Y')}."
        if self.extra_days > 0:
            msg += f"\n Returned {self.extra_days} day(s) late."
            msg += f"\n Penalty applied: ₹{self.penalty_amount:.2f} (₹{self.penalty_per_day}/day)"
        else:
            msg += "\n Returned within allowed period (No penalty)."

        self.issue_id.message_post(body=msg)

        return {'type': 'ir.actions.act_window_close'}
