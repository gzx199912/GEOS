

========================= ====================================================================================================================================================== ================================ ================================================================ 
Name                      Type                                                                                                                                                   Registered On                    Description                                                      
========================= ====================================================================================================================================================== ================================ ================================================================ 
maxStableDt               real64                                                                                                                                                                                  Value of the Maximum Stable Timestep for this solver.            
meshTargets               geos_mapBase<std_pair<string, string >, LvArray_Array<string, 1, camp_int_seq<long, 0l>, int, LvArray_ChaiBuffer>, std_integral_constant<bool, true> >                                  MeshBody/Region combinations that the solver will be applied to. 
facePressure_n            real64_array                                                                                                                                           :ref:`DATASTRUCTURE_faceManager` Face pressure at the previous converged time step                
LinearSolverParameters    node                                                                                                                                                                                    :ref:`DATASTRUCTURE_LinearSolverParameters`                      
NonlinearSolverParameters node                                                                                                                                                                                    :ref:`DATASTRUCTURE_NonlinearSolverParameters`                   
SolverStatistics          node                                                                                                                                                                                    :ref:`DATASTRUCTURE_SolverStatistics`                            
========================= ====================================================================================================================================================== ================================ ================================================================ 


