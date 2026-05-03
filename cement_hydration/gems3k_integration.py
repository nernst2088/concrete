#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEMS3K integration for cement hydration simulation
Provides interface to GEMS3K thermodynamic modeling library
"""

import os
import sys
import logging
import numpy as np
from ctypes import cdll, c_char_p, c_double, c_long, byref, POINTER, c_void_p

# config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gems3k_integration')

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GEMS3KInterface:
    def __init__(self, gems3k_lib_path=None):
        """Initialize GEMS3K interface
        
        Args:
            gems3k_lib_path: Path to GEMS3K library
        """
        self.gems3k_lib = None
        self.node = None
        self.initialized = False
        
        # Try to load GEMS3K library
        if gems3k_lib_path:
            self._load_library(gems3k_lib_path)
        else:
            # Try to find library in default locations
            default_paths = [
                os.path.join(os.path.dirname(__file__), 'libgems3k.so'),
                os.path.join(os.path.dirname(__file__), 'libgems3k.dll'),
                '/usr/local/lib/libgems3k.so',
                'C:\\Program Files\\GEMS3K\\libgems3k.dll'
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    if self._load_library(path):
                        break
        
        if not self.gems3k_lib:
            logger.warning("GEMS3K library not found. Using fallback thermodynamic calculations.")
    
    def _load_library(self, lib_path):
        """Load GEMS3K library
        
        Args:
            lib_path: Path to GEMS3K library
            
        Returns:
            bool: True if library loaded successfully
        """
        try:
            self.gems3k_lib = cdll.LoadLibrary(lib_path)
            logger.info(f"Loaded GEMS3K library from {lib_path}")
            
            # Define function prototypes
            self._define_functions()
            
            # Create TNode instance
            self.node = self.gems3k_lib.TNode_new()
            if self.node:
                logger.info("Created TNode instance successfully")
                return True
            else:
                logger.error("Failed to create TNode instance")
                return False
        except Exception as e:
            logger.error(f"Error loading GEMS3K library: {e}")
            return False
    
    def _define_functions(self):
        """Define GEMS3K function prototypes"""
        if not self.gems3k_lib:
            return
        
        # TNode constructor and destructor
        self.gems3k_lib.TNode_new.restype = c_void_p
        self.gems3k_lib.TNode_delete.argtypes = [c_void_p]
        
        # GEM_init functions
        self.gems3k_lib.GEM_init.argtypes = [c_void_p, c_char_p]
        self.gems3k_lib.GEM_init.restype = c_long
        
        # GEM_run function
        self.gems3k_lib.GEM_run.argtypes = [c_void_p, c_long]
        self.gems3k_lib.GEM_run.restype = c_long
        
        # GEM_read_dbr function
        self.gems3k_lib.GEM_read_dbr.argtypes = [c_void_p, c_char_p, c_long]
        self.gems3k_lib.GEM_read_dbr.restype = c_long
        
        # GEM_write_dbr function
        self.gems3k_lib.GEM_write_dbr.argtypes = [c_void_p, c_char_p, c_long, c_long, c_long]
        
        # GEM_to_MT function
        self.gems3k_lib.GEM_to_MT.argtypes = [
            c_void_p, POINTER(c_long), POINTER(c_long), POINTER(c_long),
            POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
            POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
            POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
            POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
            POINTER(c_double), POINTER(c_double)
        ]
        
        # GEM_from_MT function
        self.gems3k_lib.GEM_from_MT.argtypes = [
            c_void_p, c_long, c_long, c_double, c_double, c_double, c_double,
            POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)
        ]
        
        # Thermodynamic data access functions
        self.gems3k_lib.DC_G0.argtypes = [c_void_p, c_long, c_double, c_double, c_long]
        self.gems3k_lib.DC_G0.restype = c_double
        
        self.gems3k_lib.DC_H0.argtypes = [c_void_p, c_long, c_double, c_double]
        self.gems3k_lib.DC_H0.restype = c_double
        
        self.gems3k_lib.DC_S0.argtypes = [c_void_p, c_long, c_double, c_double]
        self.gems3k_lib.DC_S0.restype = c_double
        
        self.gems3k_lib.DC_Cp0.argtypes = [c_void_p, c_long, c_double, c_double]
        self.gems3k_lib.DC_Cp0.restype = c_double
        
        # Phase and component lookup functions
        self.gems3k_lib.IC_name_to_xCH.argtypes = [c_void_p, c_char_p]
        self.gems3k_lib.IC_name_to_xCH.restype = c_long
        
        self.gems3k_lib.DC_name_to_xCH.argtypes = [c_void_p, c_char_p]
        self.gems3k_lib.DC_name_to_xCH.restype = c_long
        
        self.gems3k_lib.Ph_name_to_xCH.argtypes = [c_void_p, c_char_p]
        self.gems3k_lib.Ph_name_to_xCH.restype = c_long
    
    def initialize(self, ipm_files_lst_name):
        """Initialize GEMS3K with input files
        
        Args:
            ipm_files_lst_name: Path to IPM files list
            
        Returns:
            bool: True if initialization successful
        """
        if not self.gems3k_lib or not self.node:
            logger.warning("GEMS3K library not available. Cannot initialize.")
            return False
        
        try:
            result = self.gems3k_lib.GEM_init(self.node, ipm_files_lst_name.encode('utf-8'))
            if result == 0:
                self.initialized = True
                logger.info("GEMS3K initialized successfully")
                return True
            else:
                logger.error(f"GEMS3K initialization failed with code: {result}")
                return False
        except Exception as e:
            logger.error(f"Error initializing GEMS3K: {e}")
            return False
    
    def run_calculation(self, use_primal_sol=True):
        """Run GEMS3K calculation
        
        Args:
            use_primal_sol: Use primal solution for initial approximation
            
        Returns:
            long: Node status code
        """
        if not self.initialized:
            logger.warning("GEMS3K not initialized. Cannot run calculation.")
            return -1
        
        try:
            result = self.gems3k_lib.GEM_run(self.node, 1 if use_primal_sol else 0)
            logger.info(f"GEMS3K calculation completed with status: {result}")
            return result
        except Exception as e:
            logger.error(f"Error running GEMS3K calculation: {e}")
            return -1
    
    def read_dbr_file(self, dbr_file_path, file_type=0):
        """Read DBR file
        
        Args:
            dbr_file_path: Path to DBR file
            file_type: File type (0=text, 1=binary, 2=json)
            
        Returns:
            long: Result code
        """
        if not self.initialized:
            logger.warning("GEMS3K not initialized. Cannot read DBR file.")
            return -1
        
        try:
            result = self.gems3k_lib.GEM_read_dbr(self.node, dbr_file_path.encode('utf-8'), file_type)
            if result == 0:
                logger.info(f"Successfully read DBR file: {dbr_file_path}")
            else:
                logger.error(f"Failed to read DBR file: {dbr_file_path}, code: {result}")
            return result
        except Exception as e:
            logger.error(f"Error reading DBR file: {e}")
            return -1
    
    def write_dbr_file(self, dbr_file_path, file_type=0, with_comments=True, brief_mode=False):
        """Write DBR file
        
        Args:
            dbr_file_path: Path to DBR file
            file_type: File type (0=text, 1=binary, 2=json)
            with_comments: Include comments
            brief_mode: Brief mode
        """
        if not self.initialized:
            logger.warning("GEMS3K not initialized. Cannot write DBR file.")
            return
        
        try:
            self.gems3k_lib.GEM_write_dbr(
                self.node, 
                dbr_file_path.encode('utf-8'), 
                file_type, 
                1 if with_comments else 0, 
                1 if brief_mode else 0
            )
            logger.info(f"Successfully wrote DBR file: {dbr_file_path}")
        except Exception as e:
            logger.error(f"Error writing DBR file: {e}")
    
    def get_thermodynamic_data(self, component_name, pressure=1e5, temperature=298.15):
        """Get thermodynamic data for a component
        
        Args:
            component_name: Component name
            pressure: Pressure in Pa
            temperature: Temperature in K
            
        Returns:
            dict: Thermodynamic data
        """
        if not self.initialized:
            logger.warning("GEMS3K not initialized. Using fallback thermodynamic data.")
            return self._fallback_thermodynamic_data(component_name)
        
        try:
            # Get component index
            xCH = self.gems3k_lib.DC_name_to_xCH(self.node, component_name.encode('utf-8'))
            if xCH == -1:
                logger.warning(f"Component {component_name} not found in GEMS3K database. Using fallback data.")
                return self._fallback_thermodynamic_data(component_name)
            
            # Get thermodynamic properties
            G0 = self.gems3k_lib.DC_G0(self.node, xCH, pressure, temperature, 0)  # 0 for J/mol
            H0 = self.gems3k_lib.DC_H0(self.node, xCH, pressure, temperature)
            S0 = self.gems3k_lib.DC_S0(self.node, xCH, pressure, temperature)
            Cp0 = self.gems3k_lib.DC_Cp0(self.node, xCH, pressure, temperature)
            
            return {
                'G0': G0,
                'H0': H0,
                'S0': S0,
                'Cp0': Cp0,
                'pressure': pressure,
                'temperature': temperature
            }
        except Exception as e:
            logger.error(f"Error getting thermodynamic data: {e}")
            return self._fallback_thermodynamic_data(component_name)
    
    def _fallback_thermodynamic_data(self, component_name):
        """Fallback thermodynamic data when GEMS3K is not available
        
        Args:
            component_name: Component name
            
        Returns:
            dict: Fallback thermodynamic data
        """
        # Default thermodynamic data for common cement components
        fallback_data = {
            'C3S': {'G0': -2931000, 'H0': -2931000, 'S0': 209, 'Cp0': 200},
            'C2S': {'G0': -2308000, 'H0': -2308000, 'S0': 152, 'Cp0': 150},
            'C3A': {'G0': -3561000, 'H0': -3561000, 'S0': 261, 'Cp0': 250},
            'C4AF': {'G0': -5080000, 'H0': -5080000, 'S0': 374, 'Cp0': 350},
            'CH': {'G0': -986000, 'H0': -986000, 'S0': 83, 'Cp0': 87},
            'H2O': {'G0': -237130, 'H0': -285830, 'S0': 69.91, 'Cp0': 75.3},
            'CSH': {'G0': -2723000, 'H0': -2723000, 'S0': 210, 'Cp0': 200},
            'ettringite': {'G0': -17535000, 'H0': -17535000, 'S0': 1939, 'Cp0': 1000},
            'monosulphate': {'G0': -8750000, 'H0': -8750000, 'S0': 594, 'Cp0': 500}
        }
        
        return fallback_data.get(component_name, {
            'G0': 0, 'H0': 0, 'S0': 0, 'Cp0': 0
        })
    
    def calculate_reaction_enthalpy(self, reactants, products, pressure=1e5, temperature=298.15):
        """Calculate reaction enthalpy
        
        Args:
            reactants: Dict of reactants {component: moles}
            products: Dict of products {component: moles}
            pressure: Pressure in Pa
            temperature: Temperature in K
            
        Returns:
            float: Reaction enthalpy in J/mol
        """
        try:
            total_enthalpy = 0
            
            # Calculate enthalpy of reactants
            for component, moles in reactants.items():
                data = self.get_thermodynamic_data(component, pressure, temperature)
                total_enthalpy -= moles * data['H0']  # Reactants are subtracted
            
            # Calculate enthalpy of products
            for component, moles in products.items():
                data = self.get_thermodynamic_data(component, pressure, temperature)
                total_enthalpy += moles * data['H0']  # Products are added
            
            return total_enthalpy
        except Exception as e:
            logger.error(f"Error calculating reaction enthalpy: {e}")
            return 0.0
    
    def calculate_equilibrium_constant(self, reactants, products, pressure=1e5, temperature=298.15):
        """Calculate equilibrium constant
        
        Args:
            reactants: Dict of reactants {component: moles}
            products: Dict of products {component: moles}
            pressure: Pressure in Pa
            temperature: Temperature in K
            
        Returns:
            float: Equilibrium constant
        """
        try:
            R = 8.314  # Gas constant in J/(mol·K)
            
            # Calculate Gibbs free energy change
            delta_G = 0
            
            # Calculate Gibbs free energy of reactants
            for component, moles in reactants.items():
                data = self.get_thermodynamic_data(component, pressure, temperature)
                delta_G += moles * data['G0']  # Reactants are added
            
            # Calculate Gibbs free energy of products
            for component, moles in products.items():
                data = self.get_thermodynamic_data(component, pressure, temperature)
                delta_G -= moles * data['G0']  # Products are subtracted
            
            # Calculate equilibrium constant
            if temperature <= 0:
                return 0.0
            
            K = np.exp(-delta_G / (R * temperature))
            return K
        except Exception as e:
            logger.error(f"Error calculating equilibrium constant: {e}")
            return 1.0
    
    def calculate_saturation_index(self, mineral, ions, temperature=25):
        """Calculate saturation index for a mineral
        
        Args:
            mineral: Mineral name
            ions: Dict of ion concentrations {ion: concentration in mol/L}
            temperature: Temperature in °C
            
        Returns:
            float: Saturation index
        """
        try:
            # This is a simplified implementation
            # In a real GEMS3K integration, this would use GEMS3K's internal calculations
            
            # Example: For calcite (CaCO3)
            if mineral.lower() == 'calcite':
                if 'Ca2+' in ions and 'CO32-' in ions:
                    IAP = ions['Ca2+'] * ions['CO32-']
                    Ksp = 4.8e-9  # Example Ksp for calcite at 25°C
                    return np.log10(IAP / Ksp)
            
            # Example: For portlandite (Ca(OH)2)
            elif mineral.lower() == 'portlandite' or mineral.lower() == 'ch':
                if 'Ca2+' in ions and 'OH-' in ions:
                    IAP = ions['Ca2+'] * (ions['OH-'])**2
                    Ksp = 5.02e-6  # Example Ksp for portlandite at 25°C
                    return np.log10(IAP / Ksp)
            
            # Default case
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating saturation index: {e}")
            return 0.0
    
    def calculate_activity_coefficient(self, ion, concentration, temperature=25):
        """Calculate activity coefficient for an ion
        
        Args:
            ion: Ion name
            concentration: Ion concentration in mol/L
            temperature: Temperature in °C
            
        Returns:
            float: Activity coefficient
        """
        try:
            # This is a simplified implementation using Debye-Hückel theory
            # In a real GEMS3K integration, this would use GEMS3K's internal models
            
            # Ionic strength calculation (simplified)
            ionic_strength = 0.5 * (concentration * 4)  # Assuming 2+ ion
            
            # Debye-Hückel limiting law
            A = 0.509  # Debye-Hückel constant at 25°C
            z = 2  # Charge of ion
            gamma = np.exp(-A * z**2 * np.sqrt(ionic_strength) / (1 + np.sqrt(ionic_strength)))
            
            return gamma
        except Exception as e:
            logger.error(f"Error calculating activity coefficient: {e}")
            return 1.0
    
    def close(self):
        """Close GEMS3K and free resources"""
        if self.node and self.gems3k_lib:
            try:
                self.gems3k_lib.TNode_delete(self.node)
                logger.info("GEMS3K resources freed")
            except Exception as e:
                logger.error(f"Error closing GEMS3K: {e}")
        
        self.initialized = False
        self.node = None
        self.gems3k_lib = None

class GEMS3KHydrationEnhancer:
    def __init__(self, gems3k_interface=None):
        """Initialize GEMS3K hydration enhancer
        
        Args:
            gems3k_interface: GEMS3KInterface instance
        """
        if gems3k_interface:
            self.gems3k = gems3k_interface
        else:
            self.gems3k = GEMS3KInterface()
    
    def enhance_hydration_calculation(self, cement_hydration_model, mix_design, time_days, temperature=20):
        """Enhance hydration calculation using GEMS3K
        
        Args:
            cement_hydration_model: Cement hydration model instance
            mix_design: Mix design dictionary
            time_days: Hydration time in days
            temperature: Temperature in °C
            
        Returns:
            dict: Enhanced hydration results
        """
        try:
            # Calculate basic hydration degrees using existing model
            w_c = cement_hydration_model.calculate_water_cement_ratio(mix_design)
            base_degrees = cement_hydration_model.calculate_hydration_degree(time_days, temperature, w_c)
            
            # Enhance with GEMS3K thermodynamic data
            enhanced_results = {
                'hydration_degrees': base_degrees,
                'thermodynamic_data': {},
                'equilibrium_constants': {},
                'saturation_indices': {}
            }
            
            # Get thermodynamic data for key phases
            key_phases = ['C3S', 'C2S', 'C3A', 'C4AF', 'CH', 'CSH', 'ettringite']
            for phase in key_phases:
                enhanced_results['thermodynamic_data'][phase] = self.gems3k.get_thermodynamic_data(
                    phase, 
                    pressure=1e5, 
                    temperature=273.15 + temperature
                )
            
            # Calculate equilibrium constants for key reactions
            reactions = {
                'C3S_hydration': {
                    'reactants': {'C3S': 1, 'H2O': 4.4},
                    'products': {'CSH': 1, 'CH': 2}
                },
                'C2S_hydration': {
                    'reactants': {'C2S': 1, 'H2O': 3.2},
                    'products': {'CSH': 1, 'CH': 1}
                }
            }
            
            for reaction_name, reaction in reactions.items():
                enhanced_results['equilibrium_constants'][reaction_name] = self.gems3k.calculate_equilibrium_constant(
                    reaction['reactants'],
                    reaction['products'],
                    pressure=1e5,
                    temperature=273.15 + temperature
                )
            
            # Calculate saturation indices for key minerals
            # This would be more accurate with actual solution chemistry
            ions = {
                'Ca2+': 0.1,  # Example concentration
                'OH-': 0.1,   # Example concentration
                'CO32-': 1e-5 # Example concentration
            }
            
            for mineral in ['calcite', 'portlandite']:
                enhanced_results['saturation_indices'][mineral] = self.gems3k.calculate_saturation_index(
                    mineral, ions, temperature
                )
            
            return enhanced_results
        except Exception as e:
            logger.error(f"Error enhancing hydration calculation: {e}")
            # Return basic results if enhancement fails
            return {
                'hydration_degrees': cement_hydration_model.calculate_hydration_degree(time_days, temperature),
                'thermodynamic_data': {},
                'equilibrium_constants': {},
                'saturation_indices': {}
            }
    
    def optimize_mix_design(self, cement_hydration_model, base_mix_design, target_strength, temperature=20):
        """Optimize mix design using GEMS3K thermodynamic data
        
        Args:
            cement_hydration_model: Cement hydration model instance
            base_mix_design: Base mix design dictionary
            target_strength: Target compressive strength in MPa
            temperature: Temperature in °C
            
        Returns:
            dict: Optimized mix design
        """
        try:
            # This is a simplified optimization approach
            # In a real implementation, this would use more sophisticated methods
            
            optimized_mix = base_mix_design.copy()
            
            # Adjust cement content based on target strength
            current_cement = base_mix_design.get('Cement', 300)
            strength_factor = target_strength / 30  # Assuming 30 MPa with 300 kg/m³
            new_cement = current_cement * strength_factor
            new_cement = max(200, min(600, new_cement))  # Keep within reasonable range
            optimized_mix['Cement'] = new_cement
            
            # Adjust water content to maintain water-cement ratio
            w_c = cement_hydration_model.calculate_water_cement_ratio(base_mix_design)
            optimized_mix['Water'] = new_cement * w_c
            
            # Calculate thermodynamic consistency
            cement_mass = optimized_mix['Cement']
            water_mass = optimized_mix['Water']
            
            # Check if water is sufficient for hydration
            # Theoretical water requirement for full hydration is ~0.23 by mass
            theoretical_water = cement_mass * 0.23
            if water_mass < theoretical_water:
                # Add more water if needed
                optimized_mix['Water'] = theoretical_water
                logger.info(f"Adjusted water content to theoretical requirement: {theoretical_water:.2f} kg/m³")
            
            return optimized_mix
        except Exception as e:
            logger.error(f"Error optimizing mix design: {e}")
            return base_mix_design

# Example usage
if __name__ == "__main__":
    # Create GEMS3K interface
    gems3k = GEMS3KInterface()
    
    # Create enhancer
    enhancer = GEMS3KHydrationEnhancer(gems3k)
    
    # Example mix design
    mix_design = {
        'Water': 180,
        'Cement': 300,
        'Sand': 700,
        'Aggregate': 1000
    }
    
    # Example hydration model (would be replaced with actual model instance)
    class MockHydrationModel:
        def calculate_water_cement_ratio(self, mix):
            return mix.get('Water', 0) / mix.get('Cement', 1)
        
        def calculate_hydration_degree(self, time_days, temperature=20, w_c=0.5):
            return {
                'C3S': min(0.95, 1 - np.exp(-0.5 * time_days)),
                'C2S': min(0.8, 1 - np.exp(-0.2 * time_days)),
                'C3A': min(0.98, 1 - np.exp(-1.0 * time_days)),
                'C4AF': min(0.9, 1 - np.exp(-0.3 * time_days))
            }
    
    hydration_model = MockHydrationModel()
    
    # Test enhancement
    results = enhancer.enhance_hydration_calculation(hydration_model, mix_design, 7, 20)
    print("Enhanced hydration results:")
    print(f"Hydration degrees: {results['hydration_degrees']}")
    print(f"Thermodynamic data available for {len(results['thermodynamic_data'])} phases")
    
    # Test optimization
    optimized_mix = enhancer.optimize_mix_design(hydration_model, mix_design, 40)
    print("\nOptimized mix design:")
    print(f"Cement: {optimized_mix['Cement']} kg/m³")
    print(f"Water: {optimized_mix['Water']} kg/m³")
    print(f"Water-cement ratio: {hydration_model.calculate_water_cement_ratio(optimized_mix):.2f}")
    
    # Close GEMS3K
    gems3k.close()
