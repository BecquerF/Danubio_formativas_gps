from pathlib import Path
from PyPDF2 import PdfReader

path = Path('test_informe.pdf')
reader = PdfReader(path)
print('pages', len(reader.pages))
for i, page in enumerate(reader.pages, 1):
    resources = page.get('/Resources')
    xobjects = resources.get('/XObject') if resources else None
    print('page', i, 'has xobjects', xobjects is not None)
    if xobjects:
        print('  xobj count', len(xobjects))
        for name, obj in xobjects.items():
            print('   ', name, obj.get('/Subtype'))
