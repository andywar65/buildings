from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import DxfImport

# Auto-generated `LayerMapping` dictionary for Border model
poly_mapping = {
    'layer': 'layer',
    'olinetype': 'olinetype',
    'color': 'color',
    'width': 'width',
    'thickness': 'thickness',
    'geom': 'LINESTRING25D',
}

#add your path to shape file
shp_path = Path(__file__).resolve().parent.parent.parent / 'fringuello' / 'polylines.shp'
shp_str = str(shp_path)

def run(verbose=True):
    lm = LayerMapping(DxfImport, shp_str, poly_mapping, transform=True)
    lm.save(strict=True, verbose=verbose)
