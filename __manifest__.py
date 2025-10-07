{
    'name': 'Library Management',
    'version': '18.0.10.0',
    'summary': 'Library management module for handling books data and member;s detail',
    'sequence': -100,
    'description': """This Odoo 18's Library Management System offers a dashboard view that provides a comprehensive overview of your library's activity.With that dashboard user can easily acess different key feature like book,member,issue details etc.""",
    'category': 'for study purpose',
    'website': 'https://www.odoo.com',
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/library_sequence.xml',
        'data/issue_mail_template.xml',         
        'data/welcome_email_template.xml',
        'wizard/library_wizard_issue_return.xml',
        # Load actions/views before menus to satisfy references
        'views/library_book_view.xml',
        'views/library_member_view.xml',
        'views/library_issue_view.xml',
        'views/library_dashboard.xml',
        # Menus last (they reference actions above)
        'views/library_menu_view.xml',
        'report/library_issue_report.xml',    
        'report/report_library_book.xml',
        'report/report_library_member.xml',
        'report/report_library_book_issued_users.xml',
        'report/report_member_issued_books.xml',
],


    'demo': [ ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
}
