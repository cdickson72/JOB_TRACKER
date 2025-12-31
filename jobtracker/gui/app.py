# jobtracker/gui/app.py
from nicegui import ui
from jobtracker.gui.jobs.views import jobs_page
from jobtracker.gui.notes.views import notes_page
from jobtracker.gui.resumes.views import resumes_page
from jobtracker.gui.cover_letters.views import cover_letters_page   

# Add your pages/components
jobs_page()
resumes_page()
cover_letters_page()
notes_page()


# Ensure ui.run() is called in a way compatible with Python 3.14+
if __name__ in {"__main__", "__mp_main__"}:
    ui.run()

