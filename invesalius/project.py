#--------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# Copyright:    (C) 2001  Centro de Pesquisas Renato Archer
# Homepage:     http://www.softwarepublico.gov.br
# Contact:      invesalius@cti.gov.br
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
#--------------------------------------------------------------------------
#    Este programa e software livre; voce pode redistribui-lo e/ou
#    modifica-lo sob os termos da Licenca Publica Geral GNU, conforme
#    publicada pela Free Software Foundation; de acordo com a versao 2
#    da Licenca.
#
#    Este programa eh distribuido na expectativa de ser util, mas SEM
#    QUALQUER GARANTIA; sem mesmo a garantia implicita de
#    COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM
#    PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais
#    detalhes.
#--------------------------------------------------------------------------

import wx

from utils import Singleton
from presets import Presets

class Project(object):
    # Only one project will be initialized per time. Therefore, we use
    # Singleton design pattern for implementing it
    __metaclass__= Singleton
    
    def __init__(self):
        # TODO: Discuss
        # [Tati] Will this type of data be written on project file? What if user 
        # changes file name and directory? I guess no... But, who knows...
        #self.name = "Default"
        #self.dir_ = "C:\\"
        
        # Original vtkImageData, build based on medical images read.
        # To be used for general 2D slices rendering both on 2D and 3D
        # coordinate systems. It might be used, as well, for 3D raycasting.
        # rendering.
        # TODO: Discuss when this will be used.
        self.imagedata = None
        
        # Masks are related to vtkImageData
        self.mask_dict = {}
        # Predefined threshold values
        self.min_threshold = None
        self.max_threshold = None

        self.presets = Presets()
        
        # MRI ? CT?
        self.threshold_modes = self.presets.thresh_ct

        # TODO: define how we will relate these threshold values to
        # default threshold labels
        # TODO: Future +
        # Allow insertion of new threshold modes
        
        # Surfaces are related to vtkPolyDataa
        self.surface_dict = {}
        #self.surface_quality_list = ["Low", "Medium", "High", "Optimal *",
        #                             "Custom"]
        # TOOD: define how we will relate this quality possibilities to
        # values set as decimate / smooth
        # TODO: Future +
        # Allow insertion of new surface quality modes
        
        self.measure_dict = {}
        
        # TODO: Future ++
        #self.annotation_dict = {}
        
        # TODO: Future +
        # Volume rendering modes related to vtkImageData
        # this will need to be inserted both in the project and in the user
        # InVesalius configuration file
        # self.render_mode = {}
        
        self.debug = 0
        
    ####### MASK OPERATIONS
    
    def AddMask(self, index, mask):
        """
        Insert new mask (Mask) into project data.
        
        input
            @ mask: Mask associated to mask
            
        output
            @ index: index of item that was inserted
        """
        self.mask_dict[index] = mask
        
    def GetMask(self, index):
        return self.mask_dict[index]
        

    def SetAcquisitionModality(self, type_):
        if type_ == "MRI":
            self.threshold_modes = self.presets.thresh_mri
        elif type_ == "CT":
            self.threshold_modes = self.presets.thresh_ct
        else:
            print "Different Acquisition Modality!!!"


        