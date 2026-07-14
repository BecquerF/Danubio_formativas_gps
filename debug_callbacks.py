import traceback
import CEGPS_Danubio_Formativas as m

print('calling generar_informe')
try:
    result = m.generar_informe(
        1,
        'Test',
        'Tester',
        ['actividad'],
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        ['U18'],
        '2026-05-19'
    )
    print(type(result).__name__)
    print(result is not None)
    if isinstance(result, dict):
        print('keys', list(result.keys()))
        if 'data' in result:
            print('data_len', len(result['data']))
    else:
        print(result)
except Exception:
    traceback.print_exc()

print('calling descargar_tabla')
try:
    result = m.descargar_tabla(
        1, 0, 0, 0,
        'actividad', ['U18'], ['Distance'], 'Category', [], None, None, None, None, None, None, None
    )
    print(type(result).__name__)
    print(result is not None)
    if isinstance(result, dict):
        print('keys', list(result.keys()))
        if 'data' in result:
            print('data_len', len(result['data']))
    else:
        print(result)
except Exception:
    traceback.print_exc()
