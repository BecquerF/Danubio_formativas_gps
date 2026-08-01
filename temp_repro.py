import sys
sys.path.insert(0, r'C:\Users\user\Desktop\Danubio Formativas 2026\Danubio')
import CEGPS_Danubio_Formativas as app
from datetime import datetime
try:
    fecha = app.df['Date'].max().date().isoformat()
    cats = [x for x in app.df['Category'].dropna().unique()][:1]
    res = app._build_report_download_payload(
        title='Test Informe',
        author='Tester',
        sections=['actividad','actividad_promedios','acwr'],
        texto_actividad='texto A',
        texto_actividad_comparativa='texto B',
        texto_actividad_promedios='texto C',
        texto_acwr='texto D',
        texto_plyr_vs_plyr='texto E',
        texto_comparativas='texto F',
        texto_cronologico='texto G',
        categorias=cats,
        fecha_actividad=fecha,
    )
    print('result type', type(res))
    if isinstance(res, dict):
        print('keys', res.keys())
        print('filename', res.get('filename'))
except Exception:
    import traceback
    traceback.print_exc()
