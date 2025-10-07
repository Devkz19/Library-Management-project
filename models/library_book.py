from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import xlsxwriter

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Title", required=True, tracking=True)
    author = fields.Char("Author", tracking=True)
    isbn = fields.Char("ISBN", tracking=True)
    publication_date = fields.Date("Publication Date", tracking=True)
    issue_ids = fields.One2many('library.issue', 'book_id', string="Issues")

    num_copies = fields.Integer("Total Copies", tracking=True)
    available_copies = fields.Integer(string="Available Copies", compute="_compute_available_copies", store=False)
    available = fields.Boolean("Available", default=True)

    purchase_price = fields.Float("Purchase Price")
    issue_price = fields.Float("Issue Price")
    
    category = fields.Selection([
        ('fiction', 'Fiction'),
        ('nonfiction', 'Non-fiction'),
        ('sci_fi', 'Science Fiction'),
        ('history', 'History'),
        ('biography', 'Biography'),
        ('other', 'Other'),
    ], string="Category/Genre", tracking=True)

    times_issued = fields.Integer("Times Issued", compute="_compute_times_issued", store=False)
    
    _sql_constraints = [
            ('isbn_unique', 'UNIQUE(isbn)', 'The ISBN of the book must be unique!'),
            ('available_copies_positive', 'CHECK(available_copies >= 0)', 'Available copies cannot be negative!'),
        ]
    
    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_issued(self):
        if self.env['library.issue'].search([('book_id', 'in', self.ids), ('state', '=', 'confirmed')]):
            raise UserError("Cannot delete a book that is currently issued.")
        

    @api.depends('num_copies')
    def _compute_available_copies(self):
        for book in self:
            issued_count = self.env['library.issue'].search_count([
                ('book_id', '=', book.id),
                ('state', '=', 'confirmed'),
                ('issue_type', '=', 'issue')
            ])
            book.available_copies = max(book.num_copies - issued_count, 0)
    
    def print_issued_users_report(self):
        return self.env.ref('library_management.action_report_book_issued_users').report_action(self)
    
    def action_export_book_excel(self):
        for book in self:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            sheet = workbook.add_worksheet('Book Info')

            sheet.write('A1', 'Name')
            sheet.write('B1', book.name or '')
            sheet.write('A2', 'Author')
            sheet.write('B2', book.author or '')
            sheet.write('A3', 'ISBN')
            sheet.write('B3', book.isbn or '')
            sheet.write('A4', 'Publication Date')
            sheet.write('B4', str(book.publication_date) or '')
            sheet.write('A5', 'Copies')
            sheet.write('B5', book.num_copies or 0)
            sheet.write('A6', 'Available Copies')
            sheet.write('B6', book.available_copies or 0)
            sheet.write('A7', 'Category')
            sheet.write('B7', dict(book._fields['category'].selection).get(book.category, '') or '')
            sheet.write('A8', 'Purchase Price')
            sheet.write('B8', book.purchase_price or 0.0)
            sheet.write('A9', 'Issue Price')
            sheet.write('B9', book.issue_price or 0.0)

            workbook.close()
            output.seek(0)
            excel_data = output.read()
            output.close()

            # Create attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'{book.name}_info.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(excel_data),
                'res_model': 'library.book',
                'res_id': book.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
    
    @api.model
    def create(self, vals):
        record = super(LibraryBook, self).create(vals)
        if self.env.context.get('from_ui'):
            return {
                'type': 'ir.actions.client',
                'tag': 'rainbow_man',
                'params': {
                    'message': 'Book added successfully!',
                    'fadeout': 'slow',
                    'title': 'New Book 📚',
                }
            }
        return record     
    @api.depends()
    def _compute_times_issued(self):
        for book in self:
            book.times_issued = self.env['library.issue'].search_count([
                ('book_id', '=', book.id)
            ])
     
