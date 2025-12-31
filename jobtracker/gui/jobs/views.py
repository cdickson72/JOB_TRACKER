from nicegui import ui
from jobtracker.db import get_db
from jobtracker.core.job_actions import delete_job, list_jobs, create_job, get_job_by_id, update_job
from jobtracker.models import Resume, CoverLetter
from jobtracker.enums import JobStatus
from datetime import datetime, timezone
import sys


def jobs_page(parent=None):
    container = parent or ui.column()
    with container:
        ui.label('Jobs').classes('text-2xl font-bold mb-4')

        table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left', 'classes': 'max-w-[100px] truncate'},
                {'name': 'company', 'label': 'Company', 'field': 'company', 'align': 'left', 'classes': 'max-w-[150px] truncate'},
                {'name': 'title', 'label': 'Title', 'field': 'title', 'align': 'left', 'classes': 'max-w-[150px] truncate'},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'left', 'classes': 'max-w-[100px] truncate'},
                {'name': 'source', 'label': 'Source', 'field': 'source', 'align': 'left', 'classes': 'max-w-[120px] truncate'},
                {'name': 'applied_date', 'label': 'Applied', 'field': 'applied_date', 'align': 'left', 'classes': 'max-w-[100px] truncate'},
                {'name': 'resume', 'label': 'Resume', 'field': 'resume', 'align': 'left', 'classes': 'max-w-[120px] truncate'},
                {'name': 'cover_letter', 'label': 'Cover Letter', 'field': 'cover_letter', 'align': 'left', 'classes': 'max-w-[120px] truncate'},
                {'name': 'salary_range', 'label': 'Salary', 'field': 'salary_range', 'align': 'left', 'classes': 'max-w-[100px] truncate'},
                {'name': 'location', 'label': 'Location', 'field': 'location', 'align': 'left', 'classes': 'max-w-[120px] truncate'},
                {'name': 'job_url', 'label': 'URL', 'field': 'job_url', 'align': 'left', 'classes': 'max-w-[150px] truncate'},
            ],
            rows=[],
            row_key='id',
            selection='single',
        ).classes('w-full')

        def refresh():
            with get_db() as db:
                jobs = list_jobs(db)
                table.rows = [
                    {
                        'id': j.id,
                        'company': j.company,
                        'title': j.title,
                        'status': j.status,
                        'source': j.source or '-',
                        'applied_date': j.applied_date.strftime('%Y-%m-%d') if j.applied_date else '-',
                        'resume': j.resume.name if j.resume else '-',
                        'cover_letter': j.cover_letter.name if j.cover_letter else '-',
                        'salary_range': j.salary_range or '-',
                        'location': j.location or '-',
                        'job_url': j.job_url or '-',
                    }
                    for j in jobs
                ]

        def _selected_id():
            if not table.selected:
                return None
            s = table.selected[0]
            return s.get('id') if isinstance(s, dict) else s


        def open_add_dialog():
            print('DEBUG jobs: open_add_dialog called', file=sys.stderr)
            with ui.dialog() as d, ui.card().classes('w-1/2'):
                ui.label('Add Job').classes('text-lg font-medium')
                company = ui.input('Company').classes('w-full')
                title = ui.input('Title').classes('w-full')
                source = ui.input('Source').classes('w-full')
                job_url = ui.input('Job URL').classes('w-full')
                location = ui.input('Location').classes('w-full')
                salary_range = ui.input('Salary Range').classes('w-full')
                applied_date = ui.input('Applied Date (YYYY-MM-DD)').classes('w-full')

                # fetch resumes and cover letters
                with get_db() as db:
                    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
                    letters = db.query(CoverLetter).order_by(CoverLetter.created_at.desc()).all()

                # coerce IDs to plain strings for NiceGUI select compatibility
                resume_options = [{'label': r.name, 'value': str(r.id)} for r in resumes]
                cover_options = [{'label': cl.name, 'value': str(cl.id)} for cl in letters]
                print('DEBUG jobs: resume_options=', resume_options, file=sys.stderr)
                if resume_options:
                    print('DEBUG jobs: resume default value=', resume_options[0]['value'], 'type=', type(resume_options[0]['value']), file=sys.stderr)

                if not resume_options:
                    ui.label('No resumes available — add one in Resumes').classes('text-sm text-gray-600')
                    resume_select = ui.select(options=[], label='Resume')
                else:
                    # create select first, then set value to avoid NiceGUI validation issues
                    resume_select = ui.select(options=resume_options, label='Resume')
                    try:
                        resume_select.value = str(resume_options[0]['value'])
                    except Exception:
                        pass

                if not cover_options:
                    ui.label('No cover letters available — add one in Cover Letters').classes('text-sm text-gray-600')
                    cover_select = ui.select(options=[], label='Cover Letter')
                else:
                    cover_select = ui.select(options=cover_options, label='Cover Letter')
                    try:
                        cover_select.value = str(cover_options[0]['value'])
                    except Exception:
                        pass

                def submit():
                    print('DEBUG jobs: submit add called', file=sys.stderr)
                    ad = applied_date.value.strip()
                    try:
                        applied_dt = datetime.strptime(ad, '%Y-%m-%d').replace(tzinfo=timezone.utc) if ad else None
                    except Exception:
                        applied_dt = None

                    with get_db() as db:
                        create_job(
                            db,
                            company=company.value,
                            title=title.value,
                            source=source.value or None,
                            job_url=job_url.value or None,
                            location=location.value or None,
                            salary_range=salary_range.value or None,
                            applied_date=applied_dt,
                            resume_id=resume_select.value,
                            cover_letter_id=cover_select.value,
                        )
                    ui.notify('Job added')
                    d.close()
                    refresh()

                ui.button('Add', on_click=submit)
                ui.button('Cancel', on_click=d.close)
            d.open()

        def delete_selected():
            print('DEBUG jobs: delete_selected called', file=sys.stderr)
            if not table.selected:
                ui.notify('Select a job first', type='warning')
                return
            job_id = _selected_id()
            with get_db() as db:
                delete_job(db, job_id)
            ui.notify('Job deleted')
            refresh()

        def open_update_dialog():
            print('DEBUG jobs: open_update_dialog called', file=sys.stderr)
            if not table.selected:
                ui.notify('Select a job first', type='warning')
                return
            job_id = _selected_id()
            with get_db() as db:
                job = get_job_by_id(db, job_id)
                if not job:
                    ui.notify('Job not found', type='negative')
                    return

            with ui.dialog() as d, ui.card().classes('w-1/2'):
                ui.label('Update Job').classes('text-lg font-medium')
                company = ui.input('Company', value=job.company).classes('w-full')
                title = ui.input('Title', value=job.title).classes('w-full')
                source = ui.input('Source', value=job.source or '').classes('w-full')
                job_url = ui.input('Job URL', value=job.job_url or '').classes('w-full')
                location = ui.input('Location', value=job.location or '').classes('w-full')
                salary_range = ui.input('Salary Range', value=job.salary_range or '').classes('w-full')
                applied_date = ui.input('Applied Date (YYYY-MM-DD)', value=(job.applied_date.strftime('%Y-%m-%d') if job.applied_date else '')).classes('w-full')

                # resume/cover current lists
                with get_db() as db:
                    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
                    letters = db.query(CoverLetter).order_by(CoverLetter.created_at.desc()).all()

                resume_options = [{'label': r.name, 'value': str(r.id)} for r in resumes]
                cover_options = [{'label': cl.name, 'value': str(cl.id)} for cl in letters]
                print('DEBUG jobs: (update) resume_options=', resume_options, file=sys.stderr)
                if resume_options:
                    print('DEBUG jobs: (update) job.resume_id=', job.resume_id, 'type=', type(job.resume_id), file=sys.stderr)

                if not resume_options:
                    ui.label('No resumes available — add one in Resumes').classes('text-sm text-gray-600')
                    resume_select = ui.select(options=[], label='Resume')
                else:
                    resume_select = ui.select(options=resume_options, label='Resume')
                    try:
                        resume_select.value = str(job.resume_id) if job.resume_id else str(resume_options[0]['value'])
                    except Exception:
                        pass

                if not cover_options:
                    ui.label('No cover letters available — add one in Cover Letters').classes('text-sm text-gray-600')
                    cover_select = ui.select(options=[], label='Cover Letter')
                else:
                    cover_select = ui.select(options=cover_options, label='Cover Letter')
                    try:
                        cover_select.value = str(job.cover_letter_id) if job.cover_letter_id else str(cover_options[0]['value'])
                    except Exception:
                        pass

                def submit_update():
                    print('DEBUG jobs: submit_update called', file=sys.stderr)
                    ad = applied_date.value.strip()
                    try:
                        applied_dt = datetime.strptime(ad, '%Y-%m-%d').replace(tzinfo=timezone.utc) if ad else None
                    except Exception:
                        applied_dt = None

                    with get_db() as db:
                        update_job(
                            db,
                            job,
                            company=company.value,
                            title=title.value,
                            source=source.value or None,
                            job_url=job_url.value or None,
                            location=location.value or None,
                            salary_range=salary_range.value or None,
                            applied_date=applied_dt,
                            resume_id=resume_select.value,
                            cover_letter_id=cover_select.value,
                        )
                    ui.notify('Job updated')
                    d.close()
                    refresh()

                ui.button('Update', on_click=submit_update)
                ui.button('Cancel', on_click=d.close)
            d.open()

        def change_status_selected():
            print('DEBUG jobs: change_status_selected called', file=sys.stderr)
            if not table.selected:
                ui.notify('Select a job first', type='warning')
                return
            job_id = _selected_id()
            with get_db() as db:
                job = get_job_by_id(db, job_id)
                if not job:
                    ui.notify('Job not found', type='negative')
                    return

            with ui.dialog() as d, ui.card().classes('w-1/4'):
                ui.label('Change Status').classes('text-lg font-medium')
                status_options = [{'label': s.value, 'value': s.value} for s in JobStatus]
                status_select = ui.select(options=status_options, label='Status', value=job.status)

                def submit_status():
                    print('DEBUG jobs: submit_status called', file=sys.stderr)
                    new_status = status_select.value
                    with get_db() as db:
                        j = db.query(type(job)).filter(type(job).id == job.id).first()
                        if not j:
                            ui.notify('Job not found', type='negative')
                            return
                        j.status = new_status
                        j.last_updated = datetime.now(timezone.utc)
                        try:
                            db.commit()
                        except Exception:
                            db.rollback()
                            raise
                    ui.notify('Status updated')
                    d.close()
                    refresh()

                ui.button('Set', on_click=submit_status)
                ui.button('Cancel', on_click=d.close)
            d.open()

        with ui.row().classes('mt-4'):
            ui.button('Refresh', on_click=refresh)
            ui.button('Add', on_click=open_add_dialog)
            ui.button('Update', on_click=open_update_dialog)
            ui.button('Status', on_click=change_status_selected)
            ui.button('Delete', color='negative', on_click=delete_selected)



        refresh()

