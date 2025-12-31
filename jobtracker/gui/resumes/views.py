from nicegui import ui
from jobtracker.db import get_db
from jobtracker.models import Resume
from datetime import datetime, timezone


def resumes_page(parent=None):
    container = parent or ui.column()
    with container:
        ui.label('Resumes').classes('text-2xl font-bold mb-4')

        table = ui.table(
        columns=[
            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left', 'classes': 'max-w-[300px] truncate'},
            {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left', 'classes': 'max-w-[200px] truncate'},
            {'name': 'tags', 'label': 'Tags', 'field': 'tags', 'align': 'left', 'classes': 'max-w-[250px] truncate'},
            {'name': 'file_path', 'label': 'File Path', 'field': 'file_path', 'align': 'left', 'classes': 'max-w-[450px] truncate'},
            {'name': 'created_at', 'label': 'Created (UTC)', 'field': 'created_at', 'align': 'left', 'classes': 'max-w-[150px] truncate'},
        ],
        rows=[],
        row_key='id',
        selection='single',
    ).classes('w-full')

        def refresh():
            with get_db() as db:
                resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
                table.rows = [
                    {
                        'id': r.id,
                        'name': r.name,
                        'tags': r.tags or '-',
                        'file_path': r.file_path,
                        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    for r in resumes
                ]

        def add_resume_dialog():
            with ui.dialog() as d, ui.card().classes('w-1/2'):
                ui.label('Add Resume').classes('text-lg font-medium')
                name = ui.input('Name').classes('w-full')
                file_path = ui.input('File path').classes('w-full')
                tags = ui.input('Tags (comma-separated)').classes('w-full')

                def submit():
                    with get_db() as db:
                        r = Resume(name=name.value, file_path=file_path.value, tags=tags.value or None, created_at=datetime.now(timezone.utc))
                        try:
                            db.add(r)
                            db.commit()
                            db.refresh(r)
                        except Exception:
                            db.rollback()
                            raise
                    ui.notify('Resume added')
                    d.close()
                    refresh()

                ui.button('Add', on_click=submit)
                ui.button('Cancel', on_click=d.close)
            d.open()

        def _selected_id():
            if not table.selected:
                return None
            s = table.selected[0]
            return s.get('id') if isinstance(s, dict) else s


        def remove_selected():
            if not table.selected:
                ui.notify('Select a resume first', type='warning')
                return
            resume_id = _selected_id()
            with get_db() as db:
                r = db.query(Resume).filter(Resume.id == resume_id).first()
                if not r:
                    ui.notify('Resume not found', type='negative')
                    return
                if r.jobs:
                    ui.notify('Cannot remove resume: attached to job(s)', type='warning')
                    return
                try:
                    db.delete(r)
                    db.commit()
                except Exception:
                    db.rollback()
                    raise
            ui.notify('Resume removed')
            refresh()

        def open_update_dialog():
            if not table.selected:
                ui.notify('Select a resume first', type='warning')
                return
            resume_id = _selected_id()
            with get_db() as db:
                r = db.query(Resume).filter(Resume.id == resume_id).first()
                if not r:
                    ui.notify('Resume not found', type='negative')
                    return

            with ui.dialog() as d, ui.card().classes('w-1/2'):
                ui.label('Update Resume').classes('text-lg font-medium')
                name = ui.input('Name', value=r.name).classes('w-full')
                file_path = ui.input('File path', value=r.file_path).classes('w-full')
                tags = ui.input('Tags (comma-separated)', value=r.tags or '').classes('w-full')

                def submit():
                    with get_db() as db:
                        rr = db.query(Resume).filter(Resume.id == resume_id).first()
                        if not rr:
                            ui.notify('Resume not found', type='negative')
                            return
                        rr.name = name.value
                        rr.file_path = file_path.value
                        rr.tags = tags.value or None
                        try:
                            db.commit()
                        except Exception:
                            db.rollback()
                            raise
                    ui.notify('Resume updated')
                    d.close()
                    refresh()

                ui.button('Update', on_click=submit)
                ui.button('Cancel', on_click=d.close)
            d.open()

        with ui.row().classes('mt-4'):
            ui.button('Refresh', on_click=refresh)
            ui.button('Add', on_click=add_resume_dialog)
            ui.button('Update', on_click=open_update_dialog)
            ui.button('Remove', color='negative', on_click=remove_selected)

        refresh()
