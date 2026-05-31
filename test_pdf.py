import os
import sys
import traceback

sys.path.insert(0, os.getcwd())

try:
    import base64
    import CEGPS_Danubio_Formativas as mod

    print('module loaded')
    fecha = None
    if hasattr(mod, 'df') and 'Date' in mod.df.columns:
        fecha = mod.df['Date'].max().date()
    fecha_dt = mod.pd.to_datetime(fecha).normalize() if fecha is not None else mod.df['Date'].max().normalize()
    print('fecha_dt', fecha_dt)
    sections = ['actividad', 'actividad_comparativa', 'actividad_promedios', 'acwr', 'comparativas', 'cronologico']
    report_sections = []

    for section in sections:
        fig = mod.build_section_report_fig(section, mod.df.copy(), fecha_dt, [])
        print(section, 'fig data len', len(getattr(fig, 'data', [])) if fig is not None else None)
        fig_bytes = None
        if fig is not None and getattr(fig, 'data', None):
            fig_bytes = mod.fig_to_png_bytes(fig, width=1200, height=900, scale=2)
            print(section, 'fig bytes', len(fig_bytes) if fig_bytes is not None else None)

        table_fig = mod.build_section_report_table_fig(section, mod.df.copy(), fecha_dt, [])
        print(section, 'table data len', len(getattr(table_fig, 'data', [])) if table_fig is not None else None)
        table_bytes = None
        if table_fig is not None and getattr(table_fig, 'data', None):
            table_bytes = mod.fig_to_png_bytes(table_fig, width=1200, height=520, scale=2)
            print(section, 'table bytes', len(table_bytes) if table_bytes is not None else None)

        if section in {'actividad', 'actividad_comparativa', 'acwr'}:
            report_sections.append({
                'title': mod.section_title(section),
                'text': 'test',
                'img': None,
                'table_img': table_bytes,
                'caption': 'fig',
                'table_caption': 'table'
            })
        else:
            report_sections.append({
                'title': mod.section_title(section),
                'text': 'test',
                'img': fig_bytes,
                'table_img': None,
                'caption': 'fig',
                'table_caption': 'table'
            })

    logo_bytes = base64.b64decode(mod.LOGO_BASE64) if mod.LOGO_BASE64 else None
    pdf = mod.build_report_pdf('Test', 'Tester', logo_bytes, report_sections, fecha_dt.strftime('%d/%m/%Y'), 'filters')
    print('pdf bytes', len(pdf))
    with open('test_informe.pdf', 'wb') as f:
        f.write(pdf)
    print('saved test_informe.pdf')
except Exception:
    traceback.print_exc()
