import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ElementTree

def main():
	# File paths
	path = "ViscoDruckerPragerResults.txt"
	timeFilePath = "../../../../../../../inputFiles/triaxialDriver/tables/time.geos"
	xmlFilePath = "../../../../../../../inputFiles/triaxialDriver/triaxialDriver_base.xml"
	xmlFilePath_case = "../../../../../../../inputFiles/triaxialDriver/triaxialDriver_ViscoDruckerPrager.xml"
	imposedStrainFilePath = "../../../../../../../inputFiles/triaxialDriver/tables/axialStrain.geos"
	imposedStressFilePath = "../../../../../../../inputFiles/triaxialDriver/tables/radialStress.geos"

	# Load GEOSX results
	time, ax_strain, ra_strain1, ra_strain2, ax_stress, ra_stress1, ra_stress2, newton_iter, residual_norm = np.loadtxt(
		path, skiprows=5, unpack=True)

	# Extract mechanical parameters from XML file
	tree = ElementTree.parse(xmlFilePath)
	tree_case = ElementTree.parse(xmlFilePath_case)
	model = tree_case.find('Tasks/TriaxialDriver')
	param = tree.find('Constitutive/ViscoDruckerPrager')

	bulkModulus = float(param.get("defaultBulkModulus"))
	shearModulus = float(param.get("defaultShearModulus"))
	cohesion = float(param.get("defaultCohesion"))
	frictionAngle = float(param.get("defaultFrictionAngle"))
	dilationAngle = float(param.get("defaultDilationAngle")) 
	hardeningRate = float(param.get("defaultHardeningRate"))
	relaxationTime = float(param.get("relaxationTime"))
	initialStress = float(model.get("initialStress"))
	
	# Compute Lame modulus and Young modulus
	lameModulus = bulkModulus - 2.0/3.0*shearModulus
	youngModulus = 1.0 / ( 1.0/9.0/bulkModulus + 1.0/3.0/shearModulus )

	# Friction and cohesion parameters
	frictionAngleRad = frictionAngle*np.pi/180.0
	cosFrictionAngle = np.cos(frictionAngleRad)
	sinFrictionAngle = np.sin(frictionAngleRad) 
	a = 6.0*cohesion*cosFrictionAngle/(3.0-sinFrictionAngle)
	b = 6.0*sinFrictionAngle/(3.0-sinFrictionAngle)

	# Dilation parameter
	dilationAngleRad = dilationAngle*np.pi/180.0
	sinDilationAngle = np.sin(dilationAngleRad) 
	b_dilation = 6.0*sinDilationAngle/(3.0-sinDilationAngle)
	
	# See Runesson et al. 1999, see Eq. 56
	parameter_Aep = 3.0*shearModulus + bulkModulus*b*b_dilation + hardeningRate

	# Extract loading from input tables
	imp_strain = np.loadtxt(
		imposedStrainFilePath, skiprows=0, unpack=True)

	list_ax_strain_anal = []
	numStepPerLoadingPeriod = 1000

	for i in range(0,len(imp_strain)-1):
		dStrainPerStep = (imp_strain[i+1]-imp_strain[i])/numStepPerLoadingPeriod	
		loadingPeriod = np.arange(imp_strain[i],imp_strain[i+1]+dStrainPerStep,dStrainPerStep)
		list_ax_strain_anal = np.concatenate((list_ax_strain_anal, loadingPeriod), axis=0)

	# Extract time from input tables
	imp_time = np.loadtxt(
		timeFilePath, skiprows=0, unpack=True)

	list_time_anal = []
	for i in range(0,len(imp_time)-1):
		dTimePerStep = (imp_time[i+1]-imp_time[i])/numStepPerLoadingPeriod	
		timePeriod = np.arange(imp_time[i],imp_time[i+1]+dTimePerStep,dTimePerStep)
		list_time_anal = np.concatenate((list_time_anal, timePeriod), axis=0)

	# Extract radial stress loading from input tables
	imp_stress = np.loadtxt(
		imposedStressFilePath, skiprows=0, unpack=True)

	list_ra_stress_anal = imp_stress[0]*np.ones(len(list_ax_strain_anal)) #constant radial confining stress

	# Initiate radial strain and axial stress arrays
	list_ra_strain_anal = np.zeros(len(list_ax_strain_anal))
	list_ax_stress_anal = np.zeros(len(list_ax_strain_anal))	
	list_ax_stress_anal[0] = initialStress
	list_ra_strain_anal[0] = 0

	# Loop over the loading/unloading steps	
	for idx in range(1,len(list_ax_strain_anal)):
		delta_ax_strain_anal = list_ax_strain_anal[idx] - list_ax_strain_anal[idx-1]
		delta_time_anal = list_time_anal[idx]-list_time_anal[idx-1]
		delta_ra_stress_anal = 0 # constant radial confining stress

		# Elastic trial
		delta_ra_strain_anal = (delta_ra_stress_anal-lameModulus*delta_ax_strain_anal)/(2.0*lameModulus+2.0*shearModulus)
		delta_ax_stress_anal = (lameModulus+2.0*shearModulus)*delta_ax_strain_anal + lameModulus/(lameModulus+shearModulus)*(delta_ra_stress_anal-lameModulus*delta_ax_strain_anal)

		ax_stress_anal = list_ax_stress_anal[idx-1] + delta_ax_stress_anal
		ra_strain_anal = list_ra_strain_anal[idx-1] + delta_ra_strain_anal

		# Compute mean and shear stresses
		ra_stress_anal = list_ra_stress_anal[idx]
		p_anal = (ax_stress_anal + 2.0 * ra_stress_anal) / 3.0
		q_anal = -(ax_stress_anal - ra_stress_anal)

		# Plastic correction
		if(q_anal>=0): #loading
			
			F_anal = q_anal + b*p_anal - a

			if(F_anal>=0):
				
				# Variation of Perzyna visco-plastic multiplier, see Runesson et al. 1999, see Eq. 4, 80, 62, 63
				delta_lambda = delta_time_anal / relaxationTime * (F_anal/parameter_Aep)
				
				# Compute stress and strain variations
				delta_ax_strain_anal = list_ax_strain_anal[idx] - list_ax_strain_anal[idx-1]
				delta_ax_stress_anal = ( delta_ax_strain_anal-delta_lambda*(b_dilation-3.0)/3.0 ) * youngModulus 
				delta_ra_strain_anal = delta_ax_strain_anal	 - 	delta_ax_stress_anal / 2.0 / shearModulus + 3.0/2.0*delta_lambda
		
				# Compute stress and strain at actual loading step
				ax_stress_anal = list_ax_stress_anal[idx-1] + delta_ax_stress_anal
				ra_strain_anal = list_ra_strain_anal[idx-1] + delta_ra_strain_anal
		
				# Update plastic cohesion
				delta_a = hardeningRate*delta_lambda
				a += delta_a
		
		else: #unloading
			
			F_anal = -q_anal + b*p_anal - a # negative sign added to q for q<0 to obtain the absolute value

			if(F_anal>=0):
				# Variation of Perzyna visco-plastic multiplier, see Runesson et al. 1999, see Eq. 4, 80, 62, 63
				delta_lambda = delta_time_anal / relaxationTime * (F_anal/parameter_Aep)
	
				# Compute stress and strain variations
				delta_ax_strain_anal = list_ax_strain_anal[idx] - list_ax_strain_anal[idx-1]
				delta_ax_stress_anal = ( delta_ax_strain_anal-delta_lambda*(b_dilation+3.0)/3.0 ) * youngModulus 
				delta_ra_strain_anal = delta_ax_strain_anal	 - 	delta_ax_stress_anal / 2.0 / shearModulus - 3.0/2.0*delta_lambda
		
				# Compute stress and strain at actual loading step
				ax_stress_anal = list_ax_stress_anal[idx-1] + delta_ax_stress_anal
				ra_strain_anal = list_ra_strain_anal[idx-1] + delta_ra_strain_anal
		
				# Update plastic cohesion
				delta_a = hardeningRate*delta_lambda
				a += delta_a	

		list_ax_stress_anal[idx] = ax_stress_anal
		list_ra_strain_anal[idx] = ra_strain_anal
		
	# Preparing data for visualizing semi-analytical results		
	list_p_anal = (list_ax_stress_anal + 2.0 * list_ra_stress_anal) / 3.0
	list_q_anal = -(list_ax_stress_anal - list_ra_stress_anal)

	list_strain_vol_anal = list_ax_strain_anal + 2.0 * list_ra_strain_anal

	p_num = (ax_stress + 2.0 * ra_stress1) / 3.0
	q_num = -(ax_stress - ra_stress1)

	strain_vol = ax_strain + 2.0 * ra_strain1

	#Visualization parameters
	fsize = 30
	msize = 12
	lw = 6
	malpha = 0.5
	fig, ax = plt.subplots(1, 3, figsize=(37, 10))
	cmap = plt.get_cmap("tab10")

	# Plot strain versus shear stress
	ax[0].plot(-ax_strain * 100, #convert to %
		       q_num*1e-6, #convert to MPa
		       'o',
		       color=cmap(0),
		       mec='b',
		       markersize=msize,
		       alpha=malpha,
		       label='Triaxial Driver')
	ax[0].plot(-ra_strain1 * 100, 
			   q_num*1e-6, 
			   'o', 
			   color=cmap(0), 
			   mec='b', 
			   markersize=msize, 
			   alpha=malpha)
	ax[0].plot(-list_ax_strain_anal* 100,
		       list_q_anal*1e-6,
		       '-',
		       color='r',
		       mec='r',
		       markersize=msize,
		       alpha=malpha,
		       label='Semi-Analytical', linewidth=6)
	ax[0].plot(-list_ra_strain_anal * 100, 
			   list_q_anal*1e-6, 
			   '-', 
			   color='r', 
			   mec='r', 
			   markersize=msize, 
			   alpha=malpha,
			   linewidth=6)
	ax[0].set_xlabel(r'Strain (%)', size=fsize, weight="bold")
	ax[0].set_ylabel(r'Deviatoric Stress (MPa)', size=fsize, weight="bold")
	ax[0].xaxis.set_tick_params(labelsize=fsize)
	ax[0].yaxis.set_tick_params(labelsize=fsize)
	
	# Plot axial strain versus volumetric strain
	ax[1].plot(-ax_strain * 100,
		       -strain_vol * 100,
		       'o',
		       color=cmap(0),
		       mec='b',
		       markersize=msize,
		       alpha=malpha,
		       label='Triaxial Driver')
	ax[1].plot(-list_ax_strain_anal* 100,
		       -list_strain_vol_anal* 100,
		       '-',
		       color='r',
		       mec='r',
		       markersize=msize,
		       alpha=malpha,
		       label='Semi-Analytical', linewidth=6)
	ax[1].set_xlabel(r'Axial Strain (%)', size=fsize, weight="bold")
	ax[1].set_ylabel(r'Volumetric Strain (%)', size=fsize, weight="bold")
	#ax[1].legend(loc='lower right', fontsize=fsize)
	ax[1].xaxis.set_tick_params(labelsize=fsize)
	ax[1].yaxis.set_tick_params(labelsize=fsize)
	
	# Plot shear stress versus mean stress
	ax[2].plot(-p_num*1e-6,
		       q_num*1e-6,
		       'o',
		       color=cmap(0),
		       mec='b',
		       markersize=msize,
		       alpha=malpha,
		       label='Triaxial Driver')
	ax[2].plot(-list_p_anal*1e-6,
		       list_q_anal*1e-6,
		       '-',
		       color='r',
		       mec='r',
		       markersize=msize,
		       alpha=malpha,
		       label='Semi-Analytical', linewidth=6)
	ax[2].set_xlabel(r'Mean stress (MPa)', size=fsize, weight="bold")
	ax[2].set_ylabel(r'Deviatoric Stress (MPa)', size=fsize, weight="bold")
	ax[2].legend(loc='lower right', fontsize=fsize)
	ax[2].xaxis.set_tick_params(labelsize=fsize)
	ax[2].yaxis.set_tick_params(labelsize=fsize)

	plt.subplots_adjust(left=0.2, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.4)
	plt.show()
	
if __name__ == "__main__":
    main()
