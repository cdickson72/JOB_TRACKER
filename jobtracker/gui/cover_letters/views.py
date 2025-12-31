from nicegui import ui
from jobtracker.db import get_db
from jobtracker.models import CoverLetter
from datetime import datetime, timezone


def cover_letters_page(parent=None):
    container = parent or ui.column()
    with container:
        ui.label('Cover Letters').classes('text-2xl font-bold mb-4')

        table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
                {'name': 'tags', 'label': 'Tags', 'field': 'tags', 'align': 'left'},
                {'name': 'file_path', 'label': 'File Path', 'field': 'file_path', 'align': 'left'},
                {'name': 'created_at', 'label': 'Created (UTC)', 'field': 'created_at', 'align': 'left'},
            ],
            rows=[],
            row_key='id',
            selection='single',
        ).classes('w-full')

        def refresh():
            with get_db() as db:
                letters = db.query(CoverLetter).order_by(CoverLetter.created_at.desc()).all()
                table.rows = [
                    {
                        'id': cl.id,
                        'name': cl.name,
                        'tags': cl.tags or '-',
                        'file_path': cl.file_path,
                        'created_at': cl.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    for cl in letters
                ]

        def add_dialog():
            with ui.dialog() as d, ui.card().classes('w-1/2'):
                ui.label('Add Cover Letter').classes('text-lg font-medium')
                name = ui.input('Name').classes('w-full')
                file_path = ui.input('File path').classes('w-full')
                tags = ui.input('Tags (comma-separated)').classes('w-full')

                def submit():
                    with get_db() as db:
                        cl = CoverLetter(name=name.value, file_path=file_path.value, tags=tags.value or None, created_at=datetime.now(timezone.utc))
                        try:
                            db.add(cl)
                            db.commit()
                            db.refresh(cl)
                        except Exception:
                            db.rollback()
                            raise
                    ui.notify('Cover letter added')
                    d.close()
                    refresh()

                ui.button('Add', on_click=submit)
                ui.button('Cancel', on_click=d.close)
            d.open()

        def remove_selected():
            def _selected_id():
                if not table.selected:
                    return None
                s = table.selected[0]
                return s.get('id') if isinstance(s, dict) else s

            if not table.selected:
                ui.notify('Select a cover letter first', type='warning')
                return
            cl_id = _selected_id()
            with get_db() as db:
                cl = db.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
                if not cl:
                    ui.notify('Cover letter not found', type='negative')
                    return
                if cl.jobs:
                    ui.notify('Cannot remove: attached to job(s)', type='warning')
                    return
                try:
                    db.delete(cl)
                    db.commit()
                except Exception:
                    db.rollback()
                    raise
            ui.notify('Cover letter removed')
            refresh()

        def open_update_dialog():
            def _selected_id():
                if not table.selected:
                    return None
                s = table.selected[0]
                return s.get('id') if isinstance(s, dict) else s

            if not table.selected:
                ui.notify('Select a cover letter first', type='warning')
                return
            cl_id = _selected_id()
            with get_db() as db:
                cl = db.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
                if not cl:
                    ui.notify('Cover letter not found', type='negative')
                    return

            with ui.dialog() as d, ui.card().classes('w-1/2'):
                ui.label('Update Cover Letter').classes('text-lg font-medium')
                name = ui.input('Name', value=cl.name).classes('w-full')
                file_path = ui.input('File path', value=cl.file_path).classes('w-full')
                tags = ui.input('Tags (comma-separated)', value=cl.tags or '').classes('w-full')

                def submit():
                    with get_db() as db:
                        cc = db.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
                        if not cc:
                            ui.notify('Cover letter not found', type='negative')
                            return
                        cc.name = name.value
                        cc.file_path = file_path.value
                        cc.tags = tags.value or None
                        try:
                            db.commit()
                        except Exception:
                            db.rollback()
                            raise
                    ui.notify('Cover letter updated')
                    d.close()
                    refresh()

                ui.button('Update', on_click=submit)
                ui.button('Cancel', on_click=d.close)
            d.open()

        # Action buttons explicitly inside the page container
        with ui.row().classes('mt-4'):
            ui.button('Refresh', on_click=refresh)
            ui.button('Add', on_click=add_dialog)
            ui.button('Update', on_click=open_update_dialog)
            ui.button('Remove', color='negative', on_click=remove_selected)

        refresh()
