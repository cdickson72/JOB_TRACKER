from nicegui import ui
from jobtracker.db import get_db
from jobtracker.models import Job, Note
from datetime import datetime, timezone


def notes_page(parent=None):
    container = parent or ui.column()
    with container:
        ui.label('Notes').classes('text-2xl font-bold mb-4')

        job_select = ui.select(options=[], label='Select Job').classes('w-full')

        notes_table = ui.table(
            columns=[
                {'name': 'created_at', 'label': 'Created (UTC)', 'field': 'created_at', 'align': 'left'},
                {'name': 'content', 'label': 'Note', 'field': 'content', 'align': 'left'},
            ],
            rows=[],
            row_key='created_at',
        ).classes('w-full')

        def load_jobs():
            with get_db() as db:
                jobs = db.query(Job).order_by(Job.created_at.desc()).all()
                job_select.options = [{'label': f"{j.company} — {j.title}", 'value': j.id} for j in jobs]

        def refresh_notes():
            if not job_select.value:
                notes_table.rows = []
                return
            with get_db() as db:
                job = db.query(Job).filter(Job.id == job_select.value).first()
                if not job:
                    notes_table.rows = []
                    return
                notes_table.rows = [
                    {'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'), 'content': n.content} for n in sorted(job.notes, key=lambda n: n.created_at)
                ]

        def add_note_dialog():
            if not job_select.value:
                ui.notify('Choose a job first', type='warning')
                return
            with ui.dialog() as d, ui.card().classes('w-1/2'):
                ui.label('Add Note').classes('text-lg font-medium')
                content = ui.textarea('Content').classes('w-full')

                def submit():
                    with get_db() as db:
                        note = Note(job_id=job_select.value, content=content.value, created_at=datetime.now(timezone.utc))
                        try:
                            db.add(note)
                            db.commit()
                            db.refresh(note)
                        except Exception:
                            db.rollback()
                            raise
                    ui.notify('Note added')
                    d.close()
                    refresh_notes()

                ui.button('Add', on_click=submit)
                ui.button('Cancel', on_click=d.close)
            d.open()

        # Action buttons explicitly placed inside the page container
        with ui.row().classes('mt-4'):
            ui.button('Load Jobs', on_click=load_jobs)
            ui.button('Refresh Notes', on_click=refresh_notes)
            ui.button('Add Note', on_click=add_note_dialog)

        load_jobs()
        refresh_notes()
