import sys, os, glob, string
import numpy as np
import astropy as ast
import matplotlib.pyplot as plt
from pyraf import iraf

import odi_config as odi


def mask_ota(img, ota, reproj=False, deep_obj=False):
    if reproj:
      image = odi.reprojpath+'reproj_'+ota+'.'+str(img[16:])
      QR_raw = odi.fits.open(image)
      hdu_ota = QR_raw[0]
    elif deep_obj:
      image = odi.otastackpath+ota+'_stack.fits'
      refimg = odi.scaledpath+'scaled_'+ota+'.'+str(img[16:])
      QR_raw = odi.fits.open(image)
      hdu_ota = QR_raw[0]
    else:
      QR_raw = odi.fits.open(img)
      hdu_ota = QR_raw[ota] 
    
    # Mask hot pixels count greater than 58000
    hot_pix_mask = (hdu_ota.data > 58000.0).astype(int)
    # Mask dead pixels
    if deep_obj:
      dead_pix_mask = (hdu_ota.data < -900.0).astype(int)
    else:
      dead_pix_mask = (hdu_ota.data < 1.0).astype(int)
    # Mask gaps
    gaps_mask = np.isnan(hdu_ota.data).astype(int)
    
    #Calculate background stats
    bg_stats,bg_median,med_std,std_std,centers,max_box = odi.bkg_boxes(hdu_ota,100,20.0,sources=True)
    
    #print bg_median,med_std,std_std
    
    threshold = bg_median + (med_std * 3.0)
    segm_img = odi.detect_sources(hdu_ota.data, threshold, npixels=25)
    source_mask1 =  segm_img.data.astype(np.bool)
    selem = np.ones((15,15))    # dilate using a 25x25 box
    source_mask2 = odi.binary_dilation(source_mask1, selem)  
    
    full_mask = source_mask2 + hot_pix_mask + dead_pix_mask + gaps_mask
    #full_mask = segm_img.data + hot_pix_mask + dead_pix_mask + gaps_mask
    total_mask = full_mask.astype(np.bool) # turn segm_img into a mask
    
    #create numpy masked array object
    # masked_array = ma.masked_array(hdu_ota.data,mask=total_mask)
    
    if reproj:
      # if operating on the reprojected image, return background statistics instead of the mask
      # but use the mask to get rid of sources, so it's a clean measurement
      mean, median, std = odi.sigma_clipped_stats(hdu_ota.data, mask=total_mask, sigma=3.0, iters=1)
      return mean, median, std#, dead_pix_mask
    if deep_obj:
      mask_name = 'objmask_'+ota+'.fits'
      # BPM = mask_name.replace('fits','pl')
      if not os.path.isfile(bppath+mask_name):
          hdu = odi.fits.PrimaryHDU(source_mask2.astype(float))
          hdu.writeto(bppath+mask_name,clobber=True)
      
      ota_mask = 'objmask_'+ota+'.'+str(img[16:17])+'.fits'
          
      if not os.path.isfile(odi.bppath+ota_mask):
          iraf.unlearn(iraf.mscred.mscimage)
          iraf.mscred.mscimage.format='image'
          iraf.mscred.mscimage.pixmask='no'
          iraf.mscred.mscimage.verbose='no'
          iraf.mscred.mscimage.wcssource='match'
          iraf.mscred.mscimage.reference=refimg
          # iraf.mscred.mscimage.ra=rad
          # iraf.mscred.mscimage.dec=decd
          iraf.mscred.mscimage.scale=0.11
          iraf.mscred.mscimage.rotation=0.0
          iraf.mscred.mscimage.blank=0
          iraf.mscred.mscimage.interpo='linear'
          # iraf.mscred.mscimage.minterp='poly5'
          iraf.mscred.mscimage.nxbl=2048
          iraf.mscred.mscimage.nybl=2048
          iraf.mscred.mscimage.fluxcon='yes'
          iraf.mscred.mscimage(odi.bppath+mask_name,odi.bppath+ota_mask)
      
      return
    else:
      return total_mask, gaps_mask  
    QR_raw.close()
  
def main():
    pass

if __name__ == '__main__':
    main()
  
