import vtk
import wx.lib.pubsub as ps

import constants as const
import imagedata_utils as iu
from project import Project
import vtk_utils as vu
import polydata_utils as pu

class Surface():
    """
    Represent both vtkPolyData and associated properties.
    """
    general_index = -1
    def __init__(self):
        Surface.general_index += 1
        self.index = Surface.general_index
        self.polydata = None
        self.colour = None
        self.transparency = const.SURFACE_TRANSPARENCY
        self.is_shown = 1
        self.name = const.SURFACE_NAME_PATTERN %(Surface.general_index+1)

# TODO: will be initialized inside control as it is being done?
class SurfaceManager():
    """
    Responsible for:
     - creating new surfaces;
     - managing surfaces' properties;
     - removing existing surfaces.
    
    Send pubsub events to other classes:
     - GUI: Update progress status
     - volume_viewer: Sends surface actors as the are created
    
    """
    def __init__(self):
        self.actors_dict = {}
        self.__bind_events()
        
    def __bind_events(self):
        ps.Publisher().subscribe(self.AddNewActor, 'Create surface')
        ps.Publisher().subscribe(self.SetActorTransparency,
                                 'Set surface transparency')
        ps.Publisher().subscribe(self.SetActorColour,
                                 'Set surface colour')
    
    def AddNewActor(self, pubsub_evt):
        """
        Create surface actor, save into project and send it to viewer.
        """
        imagedata, colour, [min_value, max_value] = pubsub_evt.data
        quality='Optimal'
        mode = 'CONTOUR' # 'GRAYSCALE'
        
        if quality in const.SURFACE_QUALITY.keys():
            imagedata_resolution = const.SURFACE_QUALITY[quality][0]
            smooth_iterations = const.SURFACE_QUALITY[quality][1]
            smooth_relaxation_factor = const.SURFACE_QUALITY[quality][2]
            decimate_reduction = const.SURFACE_QUALITY[quality][3]

        if imagedata_resolution:
            imagedata = iu.ResampleMatrix(imagedata)
            
        pipeline_size = 3
        if decimate_reduction:
            pipeline_size += 1
        if (smooth_iterations and smooth_relaxation_factor):
            pipeline_size += 1

        # Update progress value in GUI
        UpdateProgress = vu.ShowProgress(pipeline_size)
        
        # Flip original vtkImageData
        flip = vtk.vtkImageFlip()
        flip.SetInput(imagedata)
        flip.SetFilteredAxis(1)
        flip.FlipAboutOriginOn()

        # Create vtkPolyData from vtkImageData
        if mode == "CONTOUR":
            contour = vtk.vtkContourFilter()
            contour.SetInput(flip.GetOutput())
            contour.SetValue(0, min_value) # initial threshold
            contour.SetValue(1, max_value) # final threshold
            contour.GetOutput().ReleaseDataFlagOn()
            contour.AddObserver("ProgressEvent", lambda obj,evt:
                            UpdateProgress(contour, "Generating 3D surface..."))
            polydata = contour.GetOutput()
        else: #mode == "GRAYSCALE":
            mcubes = vtk.vtkMarchingCubes()
            mcubes.SetInput(flip.GetOutput())
            mcubes.SetValue(0, 255)
            mcubes.ComputeScalarsOn()
            mcubes.ComputeGradientsOn()
            mcubes.ComputeNormalsOn()
            mcubes.ThresholdBetween(min_value, max_value)
            mcubes.GetOutput().ReleaseDataFlagOn()
            mcubes.AddObserver("ProgressEvent", lambda obj, evt:
                           UpdateProgress(contour, "Generating 3D surface..."))
            polydata = mcubes.GetOutput()
        
        # Reduce number of triangles (previous classes create a large amount)
        # Important: vtkQuadricDecimation presented better results than
        # vtkDecimatePro
        if decimate_reduction:
            decimation = vtk.vtkQuadricDecimation()
            decimation.SetInput(polydata)
            decimation.SetTargetReduction(decimate_reduction)
            decimation.GetOutput().ReleaseDataFlagOn()
            decimation.AddObserver("ProgressEvent", lambda obj, evt: 
                  UpdateProgress(decimation, "Reducing number of triangles..."))
            polydata = decimation.GetOutput()
                                
        # TODO (Paulo): Why do we need this filter?
        #triangle = vtk.vtkTriangleFilter()
        #triangle.SetInput(polydata)
        #triangle.PassLinesOn()
        #triangle.PassVertsOn()
        #triangle.GetOutput().ReleaseDataFlagOn()
        #triangle.AddObserver("ProgressEvent",
        #                      lambda obj, evt: self.__update_progress(obj))

        # Smooth surface without changing structures
        # Important: vtkSmoothPolyDataFilter presented better results than
        # vtkImageGaussianSmooth and vtkWindowedSincPolyDataFilter  
        if smooth_iterations and smooth_relaxation_factor:
            smoother = vtk.vtkSmoothPolyDataFilter()
            smoother.SetInput(polydata)
            smoother.SetNumberOfIterations(smooth_iterations)
            smoother.SetFeatureAngle(80)
            smoother.SetRelaxationFactor(smooth_relaxation_factor)
            smoother.FeatureEdgeSmoothingOn()
            smoother.BoundarySmoothingOn()
            smoother.GetOutput().ReleaseDataFlagOn()
            smoother.AddObserver("ProgressEvent", lambda obj, evt:
                               UpdateProgress(smoother, "Smoothing surface..."))
            polydata = smoother.GetOutput()
  
        # Filter used to detect and fill holes. Only fill boundary edges holes.
        #TODO: Hey! This piece of code is the same from
        # polydata_utils.FillSurfaceHole, we need to review this.
        filled_polydata = vtk.vtkFillHolesFilter()
        filled_polydata.SetInput(polydata)
        filled_polydata.SetHoleSize(500)
        filled_polydata.AddObserver("ProgressEvent", lambda obj, evt:
                               UpdateProgress(filled_polydata,
                                              "Filling polydata..."))
        polydata = filled_polydata.GetOutput()

        print "Area: %f mm2" % pu.CalculateSurfaceArea(polydata)
        print "Volume: %f mm3" % pu.CalculateSurfaceVolume(polydata)

        # Orient normals from inside to outside
        normals = vtk.vtkPolyDataNormals()
        normals.SetInput(polydata)
        normals.SetFeatureAngle(80)
        normals.AutoOrientNormalsOn()
        normals.GetOutput().ReleaseDataFlagOn()
        normals.AddObserver("ProgressEvent", lambda obj, evt:
                               UpdateProgress(normals, "Orienting normals..."))
        polydata = normals.GetOutput()
      
        # TODO (Paulo): Why do we need this filter?
        # without this the volume does not appear
        stripper = vtk.vtkStripper()
        stripper.SetInput(normals.GetOutput())
        stripper.PassThroughCellIdsOn()
        stripper.PassThroughPointIdsOn()
        stripper.AddObserver("ProgressEvent", lambda obj, evt: 
                               UpdateProgress(stripper, "Stripping surface..."))
    
        # Map polygonal data (vtkPolyData) to graphics primitives. 
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(stripper.GetOutput())
        mapper.ScalarVisibilityOff()

        # Represent an object (geometry & properties) in the rendered scene 
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        # Create Surface instance
        surface = Surface()
        surface.colour = colour
        surface.polydata = polydata
        
        # Set actor colour and transparency
        actor.GetProperty().SetColor(colour)
        actor.GetProperty().SetOpacity(1-surface.transparency)

        # Append surface into Project.surface_dict
        proj = Project()
        proj.surface_dict[surface.index] = surface
        
        # Save actor for future management tasks
        self.actors_dict[surface.index] = actor
        
        # Send actor by pubsub to viewer's render
        ps.Publisher().sendMessage('Load surface actor into viewer', (actor))
        
        ps.Publisher().sendMessage('Update status text in GUI',
                                    "Surface created.")
                                    
        ps.Publisher().sendMessage('Update surface info in GUI',
                                    (surface.index, surface.name, 
                                    surface.colour, surface.transparency))
        
    def RemoveActor(self, index):
        """
        Remove actor, according to given actor index.
        """
        ps.Publisher().sendMessage('Remove surface actor from viewer', (index))
        self.actors_dict.pop(index)
        # Remove surface from project's surface_dict
        proj = Project()
        proj.surface_dict.pop(index)

        
    def ShowActor(self, index, value):
        """
        Show or hide actor, according to given actor index and value.
        """
        self.actors_dict[index].SetVisibility(value)
        # Update value in project's surface_dict
        proj = Project()
        proj.surface_dict[index].is_shown = value
        
    def SetActorTransparency(self, pubsub_evt):
        """
        Set actor transparency (oposite to opacity) according to given actor
        index and value.
        """
        index, value = pubsub_evt.data
        self.actors_dict[index].GetProperty().SetOpacity(1-value)
        # Update value in project's surface_dict
        proj = Project()
        proj.surface_dict[index].transparency = value
        ps.Publisher().sendMessage('Render volume viewer')
        
    def SetActorColour(self, pubsub_evt):
        """
        """
        index, colour = pubsub_evt.data
        self.actors_dict[index].GetProperty().SetColor(colour)
        # Update value in project's surface_dict
        proj = Project()
        proj.surface_dict[index].colour = colour
        ps.Publisher().sendMessage('Render volume viewer')