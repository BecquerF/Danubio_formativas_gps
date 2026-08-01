import sys
sys.path.append('.')
from dash import no_update
from CEGPS_Danubio_Formativas import generar_informe, df

fecha = df['Date'].max().date().isoformat() if 'Date' in df.columns else None
res = generar_informe(
    1,
    0,
    'Test Report',
    'Tester',
    ['actividad','actividad_promedios','acwr'],
    'Actividad text',
    'Actividad comparativa text',
    'Actividad promedios text',
    'ACWR text',
    'Plyr text',
    'Comparativas text',
    'Cronologico text',
    None,
    fecha
)
print('type:', type(res))
try:
    print('repr:', repr(res))
except Exception as e:
    print('repr error', e)
print('is no_update:', res is no_update)
if hasattr(res, '__dict__'):
    print('dict keys:', list(res.__dict__.keys()))
