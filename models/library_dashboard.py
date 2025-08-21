from odoo import models, fields, api
from collections import Counter
from datetime import date

class LibraryDashboard(models.TransientModel):
    _name = 'library.dashboard'
    _description = 'Library Dashboard'
    _rec_name = 'display_name'
    
    total_books = fields.Integer(string='Total Books')
    total_members = fields.Integer(string='Total Members')
    total_issued = fields.Integer(string='Issued Books')
    total_returned = fields.Integer(string='Returned Books')
    most_issued_books = fields.Text(string='Most Issued Books')
    books_due_today = fields.Text(string='Books Due Today')
    display_name = fields.Char(string="Dashboard Name", compute='_compute_display_name', store=False)
   
    @api.depends('create_date')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"Library Dashboard - {fields.Date.context_today(record)}"

        
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Basic counts
        total_books = self.env['library.book'].search_count([])
        total_members = self.env['library.member'].search_count([])
        total_issued = self.env['library.issue'].search_count([('state', '=', 'confirmed')])
        total_returned = self.env['library.issue'].search_count([('state', '=', 'returned')])

        # Find most issued books manually (only for confirmed issues)
        issues = self.env['library.issue'].search([('state', '=', 'confirmed')])
        book_ids = [issue.book_id.id for issue in issues if issue.book_id]
        count_by_book = Counter(book_ids)

        # Get top 3 book IDs
        top_books_ids = [book_id for book_id, _ in count_by_book.most_common(3)]
        book_names = []
        books = self.env['library.book'].browse(top_books_ids)

        for book in books:
            book_names.append(book.name or "Unknown")
            
        # Books Due Today
        today = date.today()
        issue_model = self.env['library.issue']
        due_today_records = issue_model.search([
            ('return_date', '=', today),
            ('state', '=', 'confirmed')
        ])
        due_list = [f"{rec.book_id.name} - {rec.member_id.name}" for rec in due_today_records if rec.book_id and rec.member_id]
        due_text = "\n".join(due_list) if due_list else "No books due today."

        # Update dashboard fields
        res.update({
            'total_books': total_books,
            'total_members': total_members,
            'total_issued': total_issued,
            'total_returned': total_returned,
            'most_issued_books': "\n".join(book_names),
            'books_due_today': due_text, 
        })
       
# Make sure to include display_name in the result if requested
        if 'display_name' in fields_list:
            res['display_name'] = f"Library Dashboard - {fields.Date.context_today(self)}"
        
        return res
    