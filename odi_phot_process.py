#!/usr/bin/env python

import sys, os, glob, string
import numpy as np
import astropy as ast
import matplotlib.pyplot as plt
from pyraf import iraf
from tqdm import tqdm
import odi_config as odi
import glob
import shutil
import pandas as pd

# These are not acutally needed.
# We only really need one to get the inst variable

images_g = glob.glob('20*_odi_g*.fits')
images_g.sort()
#print images_g
images_r = glob.glob('20*_odi_r*.fits')
images_r.sort()
filters = ['odi_g','odi_r']

images = images_g+images_r


source = 'sdss'
inst = odi.instrument(images[0])



# Name of final stacked g image
g_img = 'GCPair-F3_odi_g.fits'
# Name of the trimmed image
g_imgr = 'GCPair-F3_odi_g.trim.fits'
#Function to trim image
odi.trim_img(g_img)

# Name of final stacked g image
r_img = 'GCPair-F3_odi_r.fits'
# Name of the trimmed image
r_imgr = 'GCPair-F3_odi_r.trim.fits'
#Function to trim image
odi.trim_img(r_img)


#Color eq steps
#First find the sdss sources that are in each stacked image
odi.full_sdssmatch(g_img,r_img,inst,gmaglim=19.0)

#Get source and background characteristics from 'derived_props.txt'
median_fwhm,median_bg_mean,median_bg_median,median_bg_std = odi.read_proc('derived_props.txt','odi_g')

#Median arimass of all dithers
airmass_g = odi.get_airmass(images_g)
#Phot sdss g sources on stacked image
odi.sdss_phot_full(g_img,median_fwhm,airmass_g)
#This has failed for me
odi.fix_wcs_full(g_img,coords='GCPair-F1_odi_g.wcs.coo')

#Repeat same steps above, but for the r stacked image
median_fwhmr,median_bg_meanr,median_bg_medianr,median_bg_stdr = odi.read_proc('derived_props.txt','odi_r')
airmass_r = odi.get_airmass(images_r)
odi.sdss_phot_full(r_img,median_fwhmr,airmass_r)
odi.fix_wcs_full(r_img,coords='GCPair-F1_odi_r.wcs.coo')

#Solve the color equations using the pair of stacked images. This was just
#taken odi_calibrate.
odi.calibrate_match(g_img,r_img,median_fwhm,median_fwhmr,airmass_g,airmass_r)



#Phot Steps g
#Find all sources using daofind
odi.find_sources_full(g_imgr,median_fwhm,median_bg_std,threshold=2.5)
#Phot found sources
odi.phot_sources_full(g_imgr,median_fwhm,airmass_g,4.5)
#Convert xy positions of sources to Ra Dec
odi.phot_sources_xy2sky(g_imgr,inst)

#Phot Steps r
odi.find_sources_full(r_imgr,median_fwhmr,median_bg_stdr,threshold=2.5)
odi.phot_sources_full(r_imgr,median_fwhmr,airmass_r,4.5)
odi.phot_sources_xy2sky(r_imgr,inst)

#Create a matched catalog of sources on the g and r frame
odi.match_phot_srcs(g_imgr,r_imgr)