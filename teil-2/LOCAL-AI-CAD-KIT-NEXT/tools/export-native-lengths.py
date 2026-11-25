"""Export CPU-derived variants of an existing native FreeCAD document."""

import argparse
import hashlib
import json
import math
import os
import stat
import sys
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def plain_path(path):
    for candidate in (path, *path.parents):
        if not os.path.lexists(candidate):
            continue
        info = candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError(f'Linked/reparse paths are not supported: {candidate}')
    return path.resolve()


def length_value(text):
    try:
        number = Decimal(text)
        approximate = float(number)
    except (InvalidOperation, ValueError, OverflowError) as error:
        raise argparse.ArgumentTypeError('Lengths must be positive finite numbers in mm') from error
    if not number.is_finite() or number <= 0 or not math.isfinite(approximate) or approximate <= 0:
        raise argparse.ArgumentTypeError('Lengths must be positive finite numbers representable by FreeCAD')
    with localcontext() as context:
        context.prec = max(1, len(number.as_tuple().digits))
        normalized = number.normalize()
    label = format(normalized, 'f') if -6 <= normalized.adjusted() < 12 else str(normalized).lower()
    token = label.replace('.', 'p').replace('+', '').replace('-', 'm')
    if len(token) > 100:
        raise argparse.ArgumentTypeError('Length has too many digits for a portable output filename')
    return number, label, token


def write_json_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def new_output(path):
    if os.path.lexists(path):
        raise FileExistsError(f'Refusing to overwrite: {path}')
    return str(path)


def file_records(directory):
    return [{'file': path.name, 'bytes': path.stat().st_size, 'sha256': digest(path),
             'cpu_derived': True}
            for path in sorted(directory.iterdir()) if path.is_file() and path.name != 'DERIVATION.json']


def input_gui_metadata(source):
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        if names.count('GuiDocument.xml') > 1:
            raise ValueError('Input has duplicate GuiDocument.xml entries')
        return archive.read('GuiDocument.xml') if 'GuiDocument.xml' in names else None


def preserve_missing_gui_metadata(native, original_gui):
    copied = False
    with zipfile.ZipFile(native, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
        names = archive.namelist()
        if names.count('GuiDocument.xml') > 1:
            raise ValueError('Saved document has duplicate GuiDocument.xml entries')
        if 'GuiDocument.xml' not in names and original_gui is not None:
            archive.writestr('GuiDocument.xml', original_gui)
            copied = True
    with zipfile.ZipFile(native) as archive:
        if archive.testzip() is not None:
            raise ValueError(f'Saved FCStd ZIP integrity failed: {native.name}')
        present = 'GuiDocument.xml' in archive.namelist()
    return {'copied_from_input_if_missing': copied, 'present_in_export': present,
            'input_gui_sha256': hashlib.sha256(original_gui).hexdigest() if original_gui is not None else None,
            'viewport_rendered_or_refitted': False}


def require_native_objects(document, args):
    for obj in document.Objects:
        proxy = getattr(obj, 'Proxy', None)
        if proxy is not None and not (type(proxy) is int and proxy == 0):
            raise ValueError(f'Python proxies are not supported: {obj.Name}')
    sheet = document.getObject(args.sheet)
    if sheet is None or sheet.TypeId != 'Spreadsheet::Sheet':
        raise ValueError(f'Expected an existing native Spreadsheet::Sheet named {args.sheet!r}')
    cell = sheet.getCellFromAlias(args.length_alias)
    if not cell:
        raise ValueError(f'Missing existing alias {args.length_alias!r} in {sheet.Name!r}')
    objects = {}
    for role, name in (('body', args.body), ('lid', args.lid)):
        obj = document.getObject(name)
        if obj is None or not hasattr(obj, 'Shape'):
            raise ValueError(f'Missing existing {role} shape object {name!r}')
        objects[role] = obj
    if objects['body'].Name == objects['lid'].Name:
        raise ValueError('Body and lid must be different existing objects')
    return sheet, cell, objects


def shape_observation(obj):
    shape = obj.Shape
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise ValueError(f'{obj.Name} must contain one valid solid')
    bounds = shape.BoundBox
    values = [float(bounds.XLength), float(bounds.YLength), float(bounds.ZLength), float(shape.Volume)]
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ValueError(f'Non-finite or empty shape measurement: {obj.Name}')
    return {'object': obj.Name, 'type_id': obj.TypeId, 'valid': True, 'solids': 1,
            'size_mm': values[:3], 'volume_mm3': values[3]}


def export_variant(App, Part, MeshPart, source, destination, source_hash, original_gui, args, length):
    _, label, token = length
    document = None
    try:
        document = App.openDocument(str(source))
        if document is None:
            raise RuntimeError('FreeCAD did not open the source document')
        sheet, cell, objects = require_native_objects(document, args)
        original_value = sheet.getContents(cell)
        sheet.set(cell, label + ' mm')
        if document.recompute() is False:
            raise RuntimeError(f'Native recompute failed for {label} mm')
        observations = {role: shape_observation(obj) for role, obj in objects.items()}
        requested_length = float(length[0])
        for role, observation in observations.items():
            if not math.isclose(observation['size_mm'][0], requested_length, rel_tol=1e-8, abs_tol=1e-6):
                raise ValueError(f'{role} X extent did not follow the requested native length {label} mm')
        files = {'document': f'enclosure-{token}-cpu-derived.FCStd'}
        for role, obj in objects.items():
            files[role + '_step'] = f'{role}-{token}.step'
            files[role + '_stl'] = f'{role}-{token}.stl'
            Part.export([obj], new_output(destination / files[role + '_step']))
            mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.01,
                                          AngularDeflection=0.1, Relative=False)
            mesh.write(new_output(destination / files[role + '_stl']))
        native = destination / files['document']
        document.saveAs(new_output(native))
        alias_value = sheet.getContents(cell)
    finally:
        if document is not None:
            App.closeDocument(document.Name)
    if digest(source) != source_hash:
        raise RuntimeError('Original source SHA changed; derived output must not be treated as successful')
    for name in files.values():
        if not (destination / name).is_file() or (destination / name).stat().st_size == 0:
            raise RuntimeError(f'Missing or empty derived export: {name}')
    return {'length_mm': label, 'cpu_derived': True, 'files': files,
            'alias_cell': cell, 'source_alias_contents': original_value, 'derived_alias_contents': alias_value,
            'shape_observations': observations,
            'gui_metadata': preserve_missing_gui_metadata(native, original_gui)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Existing native FCStd; never saved back to this path')
    parser.add_argument('destination', type=Path, help='New output directory; its parent must already exist')
    parser.add_argument('--lengths', nargs='+', type=length_value, default=['120', '140'], metavar='MM')
    parser.add_argument('--sheet', default='Spreadsheet', help='Internal object name, not its translated label')
    parser.add_argument('--body', default='Body', help='Existing body object internal name')
    parser.add_argument('--lid', default='Lid', help='Existing lid object internal name')
    parser.add_argument('--length-alias', default='LengthMM')
    parser.add_argument('--manifest', action='store_true', help='Also write a CPU-derived cad-manifest.json')
    args = parser.parse_args(argv)
    lengths = [length_value(value) if isinstance(value, str) else value for value in args.lengths]
    if len({value[0] for value in lengths}) != len(lengths):
        parser.error('--lengths must be unique (120 and 120.0 are the same length)')
    if any(not value.strip() for value in (args.sheet, args.body, args.lid, args.length_alias)):
        parser.error('Object names and the alias must be nonempty')
    try:
        source = plain_path(args.source.expanduser().absolute())
        destination = plain_path(args.destination.expanduser().absolute())
        if not source.is_file() or source.suffix.lower() != '.fcstd':
            raise ValueError('Source must be an existing FCStd file')
        if os.path.lexists(destination) or not destination.parent.is_dir():
            raise ValueError('Destination must be absent and its parent must already exist')
        source_hash = digest(source)
        original_gui = input_gui_metadata(source)
        import FreeCAD as App
        import MeshPart
        import Part
        if App.listDocuments():
            raise RuntimeError('Use a fresh FreeCAD Python process with no open documents')
    except Exception as error:
        parser.error(str(error))
    destination.mkdir(exist_ok=False)
    report = {'schema': 1, 'status': 'running', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'source_file': str(source), 'source_sha256_before': source_hash,
              'exporter_sha256': digest(Path(__file__)), 'freecad_version': list(App.Version()),
              'cpu_derived': True, 'model_inference': False, 'gpu_model_inference': False,
              'construction_code_invoked_by_exporter': False, 'reference_geometry_used': False,
              'independent_full_geometry_validation_performed': False,
              'original_job_status_changed': False, 'original_job_completion_inferred': False,
              'source_saved_by_exporter': False, 'physical_fit_or_print_validated': False,
              'spreadsheet': args.sheet, 'length_alias': args.length_alias,
              'checked_outer_length_axis': 'X',
              'body_object': args.body, 'lid_object': args.lid,
              'meshing': {'linear_deflection_mm': 0.01, 'angular_deflection_radians': 0.1, 'relative': False},
              'variants': [], 'limitations': [
                  'Shape validity and one solid do not establish full dimensional or functional correctness.',
                  'No independent STEP/STL distance, native reopen or complete task/benchmark pass is claimed.',
                  'Copied GUI metadata preserves input settings; no new viewport image or FitAll is performed.']}
    try:
        for length in lengths:
            report['variants'].append(export_variant(App, Part, MeshPart, source, destination,
                                                     source_hash, original_gui, args, length))
        if args.manifest:
            manifest = {'schema': 1, 'cpu_derived': True, 'source_sha256': source_hash,
                        'spreadsheet': args.sheet, 'body_object': args.body, 'lid_object': args.lid,
                        'length_alias': args.length_alias,
                        'documents_by_length_mm': {row['length_mm']: row['files']['document'] for row in report['variants']},
                        'variants': [{'length_mm': row['length_mm'], **row['files']} for row in report['variants']],
                        'provenance': 'All files here are later CPU-derived exports from an existing native parameter alias. No original model job is reclassified as completed; independent full checks are separate.'}
            for row in report['variants']:
                if row['length_mm'] in ('120', '140'):
                    manifest['document_' + row['length_mm']] = row['files']['document']
            write_json_new(destination / 'cad-manifest.json', manifest)
        report['status'] = 'exported_pending_independent_checks'
    except (Exception, KeyboardInterrupt) as error:
        report['status'] = 'failed'
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        report['ended_at_utc'] = datetime.now(timezone.utc).isoformat()
        try:
            report['source_sha256_after'] = digest(source)
            report['source_bytes_unchanged'] = report['source_sha256_after'] == source_hash
        except OSError as error:
            report['source_bytes_unchanged'] = False
            report['source_verification_error'] = str(error)
        if not report['source_bytes_unchanged']:
            report['status'] = 'failed'
        report['files'] = file_records(destination)
        report_path = destination / 'DERIVATION.json'
        write_json_new(report_path, report)
    print(json.dumps({'destination': str(destination), 'status': report['status'],
                      'source_bytes_unchanged': report['source_bytes_unchanged'],
                      'cpu_derived': True, 'model_inference': False,
                      'independent_full_geometry_validation_performed': False,
                      'report_sha256': digest(report_path)}, allow_nan=False))
    return 0 if report['status'] == 'exported_pending_independent_checks' else 1


if __name__ == '__main__':
    sys.exit(main())
