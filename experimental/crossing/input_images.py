"""Real rectangular crops for elongated thresholds; no geometry or pixels invented."""
import numpy as np
from PIL import Image,ImageDraw
from beforestep.observation.images import sha256_file
from beforestep.paths import ROOT
from .runtime import write


def crop_box(box, pad, width, height):
    x0, y0, x1, y1 = box
    w, h = x1-x0+1, y1-y0+1
    centre = [(x0+x1)/2, (y0+y1)/2]
    cw = min(width, int(round(w*(1+2*pad))))
    ch = min(height, max(int(round(h*(1+2*pad))), int(np.ceil(cw/2))))
    left = max(0, min(width-cw, int(round(centre[0]-cw/2))))
    top = max(0, min(height-ch, int(round(centre[1]-ch/2))))
    return [left, top, left+cw, top+ch]


def rectangular_variants(rgb, mask, box, directory, native_height, proto):
    directory = directory/'variants';directory.mkdir(parents=True,exist_ok=True)
    height, width = rgb.shape[:2]
    tight = crop_box(box, .10, width, height)
    context = crop_box(box, .25, width, height)
    target_width, target_height = box[2]-box[0]+1, box[3]-box[1]+1
    record = {'schema':'beforestep-crossing-rectangular-input/v1','upload_px':proto['inputs']['upload_px'],
              'native_object_height_px':native_height,'native_object_width_px':target_width,
              'native_ok':native_height>=proto['inputs']['min_native_px'],'variants':{},
              'crossing_quality_rule':'Whole observed long edge preserved; old height-only gate is reported separately.'}
    # Fill only the 2-D envelope of actually observed target pixels. Retain
    # original dark RGB inside it; never change the passive depth/self-check mask.
    ys,xs=np.nonzero(mask)
    from scipy.spatial import ConvexHull
    points=np.column_stack([xs,ys]);polygon=points[ConvexHull(points).vertices]
    canvas=Image.new('L',(width,height),0);ImageDraw.Draw(canvas).polygon([tuple(map(int,p)) for p in polygon],fill=255)
    image_mask=np.asarray(canvas)>127
    record['image_mask_method']='2-D convex envelope of observed target pixels; original RGB shadows retained; self-check mask unchanged'
    record['observed_mask_pixels']=int(mask.sum());record['image_mask_pixels']=int(image_mask.sum())
    for cls, bounds in [('A',tight),('B',tight),('C',context)]:
        x0,y0,x1,y1=bounds
        crop=rgb[y0:y1,x0:x1].copy()
        if cls=='B':crop[~image_mask[y0:y1,x0:x1]]=[232,232,232]
        scale=proto['inputs']['upload_px']/max(crop.shape[:2])
        size=(int(round(crop.shape[1]*scale)),int(round(crop.shape[0]*scale)))
        image=Image.fromarray(crop).resize(size,Image.Resampling.LANCZOS)
        inside_mask=int(mask[y0:y1,x0:x1].sum());total_mask=int(mask.sum())
        for repeat in (1,2):
            name=f'{cls}{repeat}';path=directory/(name+'.png');image.save(path)
            record['variants'][name]={'path':str(path.relative_to(ROOT)),'sha256':sha256_file(path),'class':cls,
                                     'repeat_idx':repeat-1,'crop_box':bounds,'uploaded_object_height_px':round(target_height*scale,1),
                                     'uploaded_object_width_px':round(target_width*scale,1),'upload_image_size_px':list(size),
                                     'observed_mask_pixels_retained':inside_mask,'observed_mask_pixels_total':total_mask}
    minimum=proto['inputs']['min_native_px']
    record['upload_ok']=all(r['uploaded_object_height_px']>=minimum for r in record['variants'].values())
    record['crossing_quality']={'mode':'rectangular_long_edge','original_height_gate_passed':record['native_ok'] and record['upload_ok'],
                               'native_long_edge_px':max(target_width,target_height),'reference_minimum_px':minimum,
                               'accepted_for_crossing_input':max(target_width,target_height)>=minimum and all(
                                   max(r['uploaded_object_width_px'],r['uploaded_object_height_px'])>=minimum
                                   and r['observed_mask_pixels_retained']==r['observed_mask_pixels_total'] for r in record['variants'].values())}
    write(directory/'variants.json',record)
    return record
