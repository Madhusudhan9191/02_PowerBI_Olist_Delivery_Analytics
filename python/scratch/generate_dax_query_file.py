import re

with open('02_PowerBI_Olist_Delivery_Analytics/powerbi/dax/measures.dax', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
parsed_measures = []
current_folder = '01_Volume_and_Spend'
current_name = None
current_body = []

for line in lines:
    if line.strip().startswith('// FOLDER:'):
        current_folder = line.strip().replace('// FOLDER:', '').strip()
        continue
    if line.strip().startswith('// =') or line.strip().startswith('// -'):
        continue
    
    m = re.match(r'^([A-Za-z0-9][A-Za-z0-9% ()\-\._★]+)\s*=\s*$', line)
    if m and not m.group(1).strip().startswith('VAR ') and not m.group(1).strip() in ['VAR', 'RETURN']:
        if current_name:
            parsed_measures.append((current_folder, current_name, '\n'.join(current_body).strip()))
        current_name = m.group(1).strip()
        current_body = []
    else:
        if current_name:
            current_body.append(line)

if current_name:
    parsed_measures.append((current_folder, current_name, '\n'.join(current_body).strip()))

out_lines = [
    '// ============================================================================',
    '// DAX Query View Script: Bulk Define All Measures in _Measures',
    '// Instructions: Paste into DAX Query View and click Update model with changes',
    '// ============================================================================',
    '',
    'DEFINE'
]

for fld, name, body in parsed_measures:
    out_lines.append(f'    MEASURE _Measures[{name}] = ')
    for bline in body.split('\n'):
        if bline.strip():
            out_lines.append('    ' + bline)
        else:
            out_lines.append('')
    out_lines.append('')

out_lines.append('EVALUATE')
out_lines.append(f'    ROW("Total Measures", {len(parsed_measures)})')
out_lines.append('')

with open('02_PowerBI_Olist_Delivery_Analytics/powerbi/dax/all_measures_dax_query_view.dax', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

print(f'Successfully wrote powerbi/dax/all_measures_dax_query_view.dax with {len(parsed_measures)} measures!')
