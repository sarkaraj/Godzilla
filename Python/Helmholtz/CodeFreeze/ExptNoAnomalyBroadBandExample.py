from ..CommonTools.Common import*
from ..CommonTools.CreateGeometry import CreateGeometry2D
from ..CommonTools.Acquisition import Acquisition2D
from ..CommonTools.Velocity import Velocity2D
from ..Inversion.TfwiLeastSquares import TfwiLeastSquares2D
import numpy as np


# Define frequency parameters (in Hertz)
freq_peak_ricker = 20
freq_max = 35
flat_spectrum = False
gaussian_spectrum = True
omega_max = 2 * Common.pi * freq_max
omega_min = 2 * Common.pi * freq_peak_ricker / 3.0
omega_mean = 2 * Common.pi * freq_peak_ricker
omega_std = (omega_max - omega_min) * 0.25
taper_pct = 0.1
dt = 0.5 / freq_max
nt = 100
domega = (2 * Common.pi) / (nt * dt)
delay = 0.1

# Create geometry object
geom2d = CreateGeometry2D(
    xdim=3.0,
    zdim=2.0,
    vmin=1.5,
    vmax=2.5,
    omega_max=omega_max,
    omega_min=omega_min
)
geom2d.set_default_params()

print("Number of grid points in X", geom2d.gridpointsX)
print("Number of grid points in Z", geom2d.gridpointsZ)
print("Number of cells in X", geom2d.ncellsX)
print("Number of cells in Z", geom2d.ncellsZ)
print("Number of pad cells in X", geom2d.ncellsX_pad)
print("Number of pad cells in Z", geom2d.ncellsZ_pad)

# Create acquisition object
skip_src = 10
skip_rcv = 1
acq2d = Acquisition2D(geometry2d=geom2d)
acq2d.set_split_spread_acquisition(source_skip=skip_src, receiver_skip=skip_rcv, max_offset=1.5)

# Create a default Velocity 2D object
vel_true = Velocity2D(geometry2d=geom2d)
vel_start = Velocity2D(geometry2d=geom2d)
ngridpoints_x = geom2d.gridpointsX
ngridpoints_z = geom2d.gridpointsZ

# Put perturbation
center_nz = int(ngridpoints_z / 2.5)
vel_true.set_constant_velocity(vel=2.3)
vel = vel_true.vel
vel[:, center_nz + 199: center_nz + 200] = 2.0
vel_true.vel = vel

vel_start.set_constant_velocity(vel=2.3)

# Create a Tfwi object
tfwilsq = TfwiLeastSquares2D(veltrue=vel_true, velstart=vel_start, acquisition=acq2d)

tfwilsq.veltrue.plot(
    title="True Model",
    pad=False,
    vmin=1.5,
    vmax=2.3,
    xlabel="X grid points",
    ylabel="Z grid points",
    savefile=Common.filepath_base + "Fig/veltrue-noanomaly.pdf"
)
tfwilsq.velstart.plot(
    title="Starting Model",
    pad=False,
    vmin=1.5,
    vmax=2.3,
    xlabel="X grid points",
    ylabel="Z grid points",
    savefile=Common.filepath_base + "Fig/velstart-noanomaly.pdf"
)
tfwilsq.veltrue.plot_difference(
    vel_other=tfwilsq.velstart,
    pad=False,
    title="Model Difference",
    xlabel="X grid points",
    ylabel="Z grid points",
    vmin=-0.5,
    vmax=0.5,
    cmap="Greys",
    savefile=Common.filepath_base + "Fig/veldiff-noanomaly.pdf"
)

omega_list = np.arange(omega_min, omega_max, (omega_max - omega_min) / 50.0).tolist()
tfwilsq.omega_list = omega_list

if not flat_spectrum:
    if not gaussian_spectrum:
        tfwilsq.set_ricker_wavelet(omega_peak=2.0 * Common.pi * freq_peak_ricker)
    else:
        tfwilsq.set_gaussian_wavelet(omega_mean=omega_mean, omega_std=omega_std)
else:
    tfwilsq.set_flat_spectrum_wavelet()

tfwilsq.apply_frequency_taper(
    omega_low=omega_min,
    omega_high=omega_max,
    omega1=omega_min + (omega_max - omega_min) * taper_pct,
    omega2=omega_max - (omega_max - omega_min) * taper_pct
)

inverted_model, inversion_metrics = tfwilsq.perform_lsm_cg(
    epsilon=0.05,
    gamma=0,
    niter=30,
    save_lsm_image=True,
    save_lsm_allimages=True,
    lsm_image_file=Common.filepath_base + "Fig/lsm-inverted-image-noanomaly-bb50-gstd0.25-taper0.1-eps0.05",
    save_lsm_adjoint_image=True,
    save_lsm_adjoint_allimages=False,
    lsm_adjoint_image_file=Common.filepath_base + "Fig/lsm-adjoint-image-noanomaly-bb50-gstd0.25-taper0.1"
)

print(inversion_metrics)
