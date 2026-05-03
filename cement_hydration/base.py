#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base class for cement hydration simulation
Contains common functionality for all cement types
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('cement_hydration')

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chloride_diffusivity import ChlorideDiffusion
from strength_prediction import MLStrengthPrediction
from particle_packing import ParticlePackingCore, ParticlePackingVisualization
from src.solution_model import SolutionModelFactory
from src.kinetic_model import KineticModelFactory
from src.config_manager import ConfigManager
from src.solution_chemistry import SolutionChemistry
from src.cemdata_reader import CemdataReader
from .gems3k_integration import GEMS3KInterface, GEMS3KHydrationEnhancer
from ..emma_integration import EMMAInterface, EMMAEnhancer

class CementHydrationBase:
    def __init__(self, cement_type):
        """Initialize cement hydration simulator
        
        Args:
            cement_type: Type of cement
        """
        # Cement type
        self.cement_type = cement_type
        
        # Cement ratio for composite systems
        self.cement_ratio = {}
        
        # Load configuration
        self.config = ConfigManager()
        
        # Solution model for activity coefficients
        solution_model_name = self.config.get('solution_model.default', 'pitzer')
        self.solution_model = SolutionModelFactory.create_model(solution_model_name)
        
        # Kinetic model for reaction rates
        kinetic_model_name = self.config.get('kinetic_model.default', 'tkinreact')
        self.kinetic_model = KineticModelFactory.create_model(kinetic_model_name)
        
        # Solution chemistry calculator
        solution_model_name = self.config.get('solution_model.default', 'pitzer')
        self.solution_chemistry = SolutionChemistry(solution_model_name)
        
        # CEMDATA database reader
        # 正确设置CEMDATA数据库路径
        cemdata_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cemdata')
        self.cemdata_reader = CemdataReader('18.1', cemdata_dir)
        
        # GEMS3K integration
        self.gems3k_interface = GEMS3KInterface()
        self.gems3k_enhancer = GEMS3KHydrationEnhancer(self.gems3k_interface)
        
        # EMMA integration
        self.emma_interface = EMMAInterface()
        self.emma_enhancer = EMMAEnhancer(self.emma_interface)
        
        # Density (kg/m³)
        self.densities = self.config.get('material_properties.densities', {
            'Water': 1000,
            'Cement': 3150,
            'Fly Ash': 2400,
            'Slag': 2900,
            'Silica Fume': 2200,
            'Kaolin': 2600,
            'CSH Seed': 2500,
            'Sand': 2650,
            'Aggregate': 2700,
            'Steel Fiber': 7850,
            'Carbon Fiber': 1800,
            'Synthetic Fiber': 1100,
            'Plant Fiber': 1500,
            'Mineral Fiber': 2800,
            'Nano SiO2': 2200,
            'Nano Al2O3': 3900,
            'Nano CaCO3': 2700,
            'Nano CaO': 3350,
            'Nano MgO': 3580,
            'Graphene': 2200,
            'Concrete': 2400
        })
        
        # Specific heat capacity (J/(kg·°C))
        self.specific_heat = self.config.get('material_properties.specific_heat', {
            'Cement': 880,
            'Water': 4186,
            'Fly Ash': 800,
            'Slag': 750,
            'Silica Fume': 700,
            'Kaolin': 800,
            'CSH Seed': 850,
            'Sand': 800,
            'Aggregate': 800,
            'Steel Fiber': 450,
            'Carbon Fiber': 700,
            'Synthetic Fiber': 1400,
            'Plant Fiber': 1300,
            'Mineral Fiber': 800,
            'Nano SiO2': 700,
            'Nano Al2O3': 880,
            'Nano CaCO3': 850,
            'Nano CaO': 900,
            'Nano MgO': 920,
            'Graphene': 700,
            'Concrete': 900
        })
        
        # Nano materials effect on hydration
        self.nano_effects = self.config.get('nano_effects', {
            'Nano SiO2': {
                'hydration_acceleration': 1.5,
                'cs_h_nucleation': 2.0,
                'pozzolanic_reactivity': 1.8,
                'strength_enhancement': 1.3
            },
            'Nano Al2O3': {
                'hydration_acceleration': 1.3,
                'afm_formation': 1.5,
                'strength_enhancement': 1.2
            },
            'Nano CaCO3': {
                'hydration_acceleration': 1.2,
                'csh_seed_effect': 1.6,
                'strength_enhancement': 1.1
            },
            'Nano CaO': {
                'hydration_acceleration': 1.8,
                'alkaline_enhancement': 2.0,
                'strength_enhancement': 1.4
            },
            'Nano MgO': {
                'hydration_acceleration': 1.1,
                'expansion_control': 1.3,
                'strength_enhancement': 1.05
            },
            'Graphene': {
                'hydration_acceleration': 1.4,
                'nucleation_sites': 2.2,
                'strength_enhancement': 1.5,
                'conductivity_enhancement': 10.0
            }
        })
        
        # Default mix design values (kg/m³)
        self.default_mix_design = self.config.get('default_mix_design', {
            'Water': 180,
            'Cement': 300,
            'Fly Ash': 0,
            'Slag': 0,
            'Silica Fume': 0,
            'Kaolin': 0,
            'CSH Seed': 0,
            'Nano SiO2': 0,
            'Nano Al2O3': 0,
            'Nano CaCO3': 0,
            'Nano CaO': 0,
            'Nano MgO': 0,
            'Graphene': 0,
            'Sand': 700,
            'Aggregate': 1000,
            'Steel Fiber': 0,
            'Carbon Fiber': 0,
            'Synthetic Fiber': 0,
            'Plant Fiber': 0,
            'Mineral Fiber': 0,
            'CaCl2': 0,
            'AlCl3': 0,
            'Na2SO4': 0,
            'NaOH': 0,
            'KOH': 0,
            'Na2CO3': 0,
            'K2CO3': 0,
            'Retarder': 0,
            'Superplasticizer': 0,
            'AirEntrainer': 0,
            'ViscosityModifier': 0
        })
        
        # Chemical admixtures effect on hydration
        self.chemical_admixtures_effects = self.config.get('chemical_admixtures_effects', {
            'CaCl2': {
                'hydration_acceleration': 1.8,
                'c3a_acceleration': 2.5,
                'freezing_point_reduction': 1.5
            },
            'AlCl3': {
                'hydration_acceleration': 1.6,
                'c3a_acceleration': 2.0,
                'setting_acceleration': 1.8
            },
            'Na2SO4': {
                'hydration_acceleration': 1.4,
                'c3a_modification': 1.2,
                'sulfate_activation': 1.5
            },
            'NaOH': {
                'hydration_acceleration': 1.5,
                'alkaline_enhancement': 2.5,
                'silicate_dissolution': 1.8
            },
            'KOH': {
                'hydration_acceleration': 1.5,
                'alkaline_enhancement': 2.5,
                'silicate_dissolution': 1.8
            },
            'Na2CO3': {
                'hydration_acceleration': 1.3,
                'alkaline_enhancement': 1.8,
                'carbonation_effect': 1.2
            },
            'K2CO3': {
                'hydration_acceleration': 1.3,
                'alkaline_enhancement': 1.8,
                'carbonation_effect': 1.2
            },
            'Retarder': {
                'hydration_retardation': 0.6,
                'setting_retardation': 0.5,
                'workability_improvement': 1.3
            },
            'Superplasticizer': {
                'water_reduction': 0.8,
                'workability_improvement': 1.5,
                'dispersion_effect': 1.2
            },
            'AirEntrainer': {
                'air_content_increase': 1.5,
                'workability_improvement': 1.2,
                'freezing_thawing_resistance': 1.3
            },
            'ViscosityModifier': {
                'viscosity_increase': 1.5,
                'segregation_reduction': 1.3,
                'bleeding_reduction': 1.4
            }
        })
        
        # Molar mass (g/mol)
        self.molar_mass = {
            'C3S': 228.31,     # Ca3SiO5
            'C2S': 172.27,     # Ca2SiO4
            'C3A': 270.21,     # Ca3Al2O6
            'C4AF': 485.97,    # Ca4Al2Fe2O10
            'C4A3S': 466.23,   # Ca4Al6SO16 (Tricalcium sulfoaluminate)
            'CaSO4': 136.14,   # Calcium sulfate (Gypsum)
            'CaSO4_05H2O': 145.15, # Calcium sulfate hemihydrate (Plaster of Paris)
            'CA': 158.04,      # CaAl2O4 (Monocalcium aluminate)
            'CA2': 222.15,     # Ca4Al2Fe2O10
            'C12A7': 1134.77,  # Ca12Al14O33 (12CaO·7Al2O3)
            'MgO': 40.30,       # Magnesium oxide
            'KH2PO4': 136.09,   # Potassium dihydrogen phosphate (MKP)
            'H2O': 18.015,      # Water
            'CSH': 226.32,      # C3S2H3 (simplified CSH)
            'CH': 74.09,        # Ca(OH)2
            'AFt': 1255.67,     # Ca6Al2(SO4)3(OH)12(H2O)26
            'AFm': 622.58,      # Ca4Al2SO10(H2O)12
            'ettringite': 1255.67, # Ca6Al2(SO4)3(OH)12·26H2O
            'monosulphate': 622.58, # Ca4Al2(SO4)(OH)12·6H2O
            'tricarboaluminate': 1186.5, # Ca6Al2(CO3)3(OH)12·26H2O
            'C3AH6': 294.22,    # Ca3Al2(OH)12
            'C4AH13': 442.33,   # Ca4Al2(OH)14·6H2O
            'C2AH8': 318.20,    # Ca2Al2(OH)10·3H2O
            'straetlingite': 354.22,  # Ca2Al2SiO2(OH)10·3H2O
            'thaumasite': 1004.6, # Ca3Si(OH)6(CO3)(SO4)·12H2O
            'ettringite_sulpho': 1255.67, # Ettringite from sulphoaluminate hydration
            'CAH10': 398.35,    # CaAl2(OH)8·6H2O
            'C2AH8': 318.20,    # Ca2Al2(OH)10·3H2O
            'C3AH6': 294.22,    # Ca3Al2(OH)12
            'AH3': 78.00,       # Al(OH)3 (Gibbsite)
            'MCPM': 252.31,     # MgKHPO4·6H2O (Monocalcium phosphate monohydrate)
            'MKP': 136.09,      # KH2PO4 (Potassium dihydrogen phosphate)
            'MgO': 40.30        # Magnesium oxide
        }
        
        # Molar volume (cm³/mol) from CEMDATA18
        self.molar_volume = {
            'C3S': 73,           # Tricalcium silicate
            'C2S': 52,           # Dicalcium silicate
            'C3A': 89,           # Tricalcium aluminate
            'C4AF': 130,         # Tetracalcium aluminoferrite
            'C4A3S': 145,         # Tricalcium sulfoaluminate
            'CaSO4': 46.9,        # Calcium sulfate (Gypsum)
            'CaSO4_05H2O': 49.5,   # Calcium sulfate hemihydrate (Plaster of Paris)
            'CA': 52.5,          # Monocalcium aluminate
            'CA2': 68.0,         # Dicalcium aluminate
            'C12A7': 350.0,      # 12CaO·7Al2O3
            'MgO': 11.25,         # Magnesium oxide
            'KH2PO4': 74.0,       # Potassium dihydrogen phosphate (MKP)
            'CSH_jennite': 78.4,  # Jennite-type C-S-H (Ca/Si=1.67)
            'CSH_tobermorite': 59, # Tobermorite-type C-S-H (Ca/Si=0.83)
            'CSH_cshq': 75,       # Q-phase C-S-H (CEMDATA18)
            'CSH_cshkn': 77,      # Kato-Nishiyama C-S-H (CEMDATA18)
            'CSH_csh3t': 70,      # 3T C-S-H (CEMDATA18)
            'CSH_csh2o': 80,      # 2O C-S-H (CEMDATA18)
            'CH': 33.06,         # Portlandite
            'AFt': 707,          # Ettringite
            'AFm': 310.1,        # Monosulphate12
            'H2O': 18.068,       # Water
            'ettringite': 707,    # Ettringite
            'monosulphate': 310.1, # Monosulphate12
            'tricarboaluminate': 650, # Tricarboaluminate
            'C3AH6': 150,        # C3AH6
            'C4AH13': 274,       # C4AH13
            'C4AH19': 371,       # C4AH19
            'C2AH7.5': 180,      # C2AH7.5
            'straetlingite': 216,  # Straetlingite
            'thaumasite': 663,    # Thaumasite
            'ettringite_sulpho': 707, # Ettringite from sulphoaluminate hydration
            'CAH10': 193,        # CaAl2(OH)8·6H2O
            'AH3': 31.96,         # Al(OH)3 (Gibbsite)
            'MCPM': 180.0,       # MgKHPO4·6H2O (Monocalcium phosphate monohydrate)
            'MKP': 74.0,          # KH2PO4 (Potassium dihydrogen phosphate)
            'MgO': 11.25,         # Magnesium oxide
            'Friedels_salt': 272,  # Friedel's salt
            'Kuzels_salt': 289,   # Kuzel's salt
            'hydrotalcite': 220,  # Hydrotalcite
            'syngenite': 128      # Syngenite
        }
        
        # Hydration heat (J/g) based on CEMDATA18
        # Calculated from ΔfH° values - adjusted to realistic values
        self.hydration_heat = {
            'C3S': -300,    # Heat of hydration for C3S (J/g) - adjusted to realistic value
            'C2S': -200,    # Heat of hydration for C2S (J/g) - adjusted to realistic value
            'C3A': -350,    # Heat of hydration for C3A (J/g) - adjusted to realistic value
            'C4AF': -250,   # Heat of hydration for C4AF (J/g) - adjusted to realistic value
            'C4A3S': -400,  # Heat of hydration for C4A3S (J/g) - adjusted to realistic value
            'CaSO4': -80,   # Heat of hydration for CaSO4 anhydrite (J/g) - adjusted to realistic value
            'CaSO4_05H2O': -150, # Heat of hydration for CaSO4·0.5H2O (J/g) - adjusted to realistic value
            'CA': -450,     # Heat of hydration for CA (J/g) - adjusted to realistic value
            'CA2': -350,    # Heat of hydration for CA2 (J/g) - adjusted to realistic value
            'C12A7': -400,  # Heat of hydration for C12A7 (J/g) - adjusted to realistic value
            'MgO': -300,     # Heat of hydration for MgO (J/g) - adjusted to realistic value
            'KH2PO4': -350  # Heat of hydration for KH2PO4 (J/g) - adjusted to realistic value
        }
        
        # Thermodynamic data from CEMDATA18
        self.thermodynamic_data = self.config.get('thermodynamic_data', {
            'C3S': {'delta_fH': -2931, 'S': 209},
            'C2S': {'delta_fH': -2308, 'S': 152},
            'C3A': {'delta_fH': -3561, 'S': 261},
            'C4AF': {'delta_fH': -5080, 'S': 374},
            'CH': {'delta_fH': -986, 'S': 83},
            'ettringite': {'delta_fH': -17535, 'S': 1939},
            'monosulphate': {'delta_fH': -8750, 'S': 594},
            'C3AH6': {'delta_fH': -5540, 'S': 292},
            'C4AH13': {'delta_fH': -8302, 'S': 711},
            'C4AH19': {'delta_fH': -10017.9, 'S': 1163},
            'CAH10': {'delta_fH': -5288.2, 'S': 151},
            'CSH_jennite': {'delta_fH': -2723, 'S': 210},
            'CSH_tobermorite': {'delta_fH': -1916, 'S': 85},
            'straetlingite': {'delta_fH': -6360, 'S': 438},
            'thaumasite': {'delta_fH': -8700, 'S': 1031},
            'Friedels_salt': {'delta_fH': -7604, 'S': 498},
            'hydrotalcite': {'delta_fH': -7196, 'S': -364}
        })
        
        # C-S-H models from CEMDATA18
        self.csh_models = self.config.get('csh_models', {
            'cshq': {'name': 'Q-phase C-S-H', 'ca_si_ratio': 1.67, 'h2o_si_ratio': 2.1, 'density': 2500, 'molar_volume': 75},
            'cshkn': {'name': 'Kato-Nishiyama C-S-H', 'ca_si_ratio': 1.5, 'h2o_si_ratio': 2.0, 'density': 2450, 'molar_volume': 77},
            'csh3t': {'name': '3T C-S-H', 'ca_si_ratio': 1.0, 'h2o_si_ratio': 1.5, 'density': 2300, 'molar_volume': 70},
            'csh2o': {'name': '2O C-S-H', 'ca_si_ratio': 0.83, 'h2o_si_ratio': 1.33, 'density': 2200, 'molar_volume': 80}
        })
        
        # Slag composition for hydration modeling
        self.slag_composition = {
            'CaO': 0.423,  # 42.3%
            'SiO2': 0.359,  # 35.9%
            'Al2O3': 0.112, # 11.2%
            'MgO': 0.08,   # 8.0%
            'Fe2O3': 0.003, # 0.3%
            'SO3': 0.002   # 0.2%
        }
        
        # Fly ash composition for hydration modeling
        self.fly_ash_composition = {
            'SiO2': 0.55,   # 55%
            'Al2O3': 0.25,  # 25%
            'Fe2O3': 0.10,  # 10%
            'CaO': 0.05,    # 5%
            'MgO': 0.02,    # 2%
            'SO3': 0.01,    # 1%
            'Others': 0.02  # 2%
        }
    
    def calculate_water_cement_ratio(self, mix_design):
        """Calculate water-cement ratio"""
        try:
            water = mix_design.get('Water', 0)
            cement = mix_design.get('Cement', 0)
            return water / cement if cement > 0 else 0
        except Exception as e:
            print(f"Error calculating water-cement ratio: {e}")
            return 0
    
    def calculate_hydration_degree(self, time_days, temperature=20, w_c=0.5, nano_materials=None, chemical_admixtures=None):
        """Calculate hydration degree of different minerals"""
        raise NotImplementedError("Subclass must implement this method")
    
    def calculate_surface_area(self, particle_size_distribution, initial_surface_area, hydration_degree):
        """Calculate surface area considering particle size distribution and hydration"""
        # Based on GEMS3K's surface area correction model
        if hydration_degree == 0:
            return initial_surface_area
        
        # Simple model: surface area increases during early hydration due to dissolution
        # then decreases as particles are consumed
        if hydration_degree < 0.3:
            # Early hydration: surface area increases
            surface_area_factor = 1 + 2 * hydration_degree
        else:
            # Later hydration: surface area decreases
            surface_area_factor = 1.6 * (1 - hydration_degree / 2)
        
        return initial_surface_area * surface_area_factor
    
    def calculate_arrhenius_factor(self, activation_energy, temperature, ref_temperature=20):
        """Calculate Arrhenius factor for temperature dependence"""
        try:
            R = 8.314  # Gas constant in J/(mol·K)
            T_ref = 273.15 + ref_temperature  # Reference temperature in K
            T = 273.15 + temperature  # Current temperature in K
            
            # Ensure temperature is not zero or negative
            if T <= 0:
                return 0
            
            return np.exp(-activation_energy/R * (1/T - 1/T_ref))
        except Exception as e:
            print(f"Error calculating Arrhenius factor: {e}")
            return 1.0
    
    def calculate_ionic_strength_effect(self, ionic_strength, bI):
        """Calculate ionic strength effect on reaction rate"""
        try:
            if bI == 0:
                return 1.0
            # Ensure ionic strength is not negative
            ionic_strength = max(0, ionic_strength)
            return (1 + ionic_strength)**bI
        except Exception as e:
            print(f"Error calculating ionic strength effect: {e}")
            return 1.0
    
    def calculate_pH_effect(self, pH, bpH):
        """Calculate pH effect on reaction rate"""
        try:
            if bpH == 0:
                return 1.0
            # Ensure pH is within reasonable range
            pH = max(0, min(14, pH))
            return 10**(bpH * (pH - 7))
        except Exception as e:
            print(f"Error calculating pH effect: {e}")
            return 1.0
    
    def calculate_affinity_term(self, saturation_index, qPR=1, mPR=0, uPR=0):
        """Calculate affinity term based on saturation index"""
        try:
            # Based on GEMS3K's TKinReact model
            if saturation_index < 1:
                # Dissolution
                return (1 - saturation_index**qPR)
            else:
                # Precipitation
                return -1 * (saturation_index**mPR - 1) * np.exp(uPR * (saturation_index - 1))
        except Exception as e:
            print(f"Error calculating affinity term: {e}")
            return 0.0
    
    def calculate_activity_coefficient(self, ion, concentration, temperature=25):
        """Calculate activity coefficient for an ion using the selected solution model"""
        return self.solution_model.calculate_activity_coefficient(ion, concentration, temperature)
    
    def set_solution_model(self, model_name):
        """Set the solution model to use"""
        self.solution_model = SolutionModelFactory.create_model(model_name)
    
    def calculate_reaction_rate(self, rate_constant, arrhenius_factor, catalytic_term, affinity_term):
        """Calculate reaction rate based on GEMS3K's approach"""
        try:
            rate = rate_constant * arrhenius_factor * catalytic_term * affinity_term
            # Ensure rate is non-negative
            return max(0, rate)
        except Exception as e:
            print(f"Error calculating reaction rate: {e}")
            return 0.0
    
    def calculate_kinetic_reaction_rate(self, time, temperature, mineral, hydration_degree, **kwargs):
        """Calculate reaction rate using the selected kinetic model"""
        return self.kinetic_model.calculate_reaction_rate(time, temperature, mineral, hydration_degree, **kwargs)
    
    def set_kinetic_model(self, model_name):
        """Set the kinetic model to use"""
        self.kinetic_model = KineticModelFactory.create_model(model_name)
    
    def calculate_pH(self, ions, temperature=25):
        """Calculate pH of a solution"""
        return self.solution_chemistry.calculate_pH(ions, temperature)
    
    def calculate_ion_concentrations(self, components, temperature=25):
        """Calculate ion concentrations from components"""
        return self.solution_chemistry.calculate_ion_concentrations(components, temperature)
    
    def calculate_ionic_strength(self, ions):
        """Calculate ionic strength of a solution"""
        return self.solution_chemistry.calculate_ionic_strength(ions)
    
    def calculate_saturation_index(self, mineral, ions, temperature=25):
        """Calculate saturation index for a mineral"""
        return self.solution_chemistry.calculate_saturation_index(mineral, ions, temperature)
    
    def calculate_buffer_capacity(self, ions, temperature=25):
        """Calculate buffer capacity of a solution"""
        return self.solution_chemistry.calculate_buffer_capacity(ions, temperature)
    
    def simulate_ion_leaching(self, initial_ions, contact_time, temperature=25):
        """Simulate ion leaching from cement paste"""
        return self.solution_chemistry.simulate_ion_leaching(initial_ions, contact_time, temperature)
    
    def get_cemdata_thermodynamic_data(self, phase_name):
        """Get thermodynamic data from CEMDATA database"""
        return self.cemdata_reader.get_thermodynamic_data(phase_name)
    
    def get_cemdata_phase_data(self, phase_name):
        """Get phase data from CEMDATA database"""
        return self.cemdata_reader.get_phase_data(phase_name)
    
    def get_cemdata_phases(self):
        """Get all phases in CEMDATA database"""
        return self.cemdata_reader.get_all_phases()
    
    def search_cemdata_phase(self, keyword):
        """Search for phases in CEMDATA database"""
        return self.cemdata_reader.search_phase(keyword)
    
    def update_thermodynamic_data_from_cemdata(self):
        """Update thermodynamic data from CEMDATA database"""
        for phase in self.thermodynamic_data:
            cemdata_data = self.cemdata_reader.get_thermodynamic_data(phase)
            if cemdata_data:
                self.thermodynamic_data[phase].update(cemdata_data)
    
    def update_hydration_heat_from_cemdata(self):
        """Update hydration heat data from CEMDATA database"""
        # 定义主要矿物的反应式
        reactions = {
            'C3S': {
                'reactants': {'C3S': 1, 'H2O': 4.4},
                'products': {'CSH': 1, 'CH': 2}
            },
            'C2S': {
                'reactants': {'C2S': 1, 'H2O': 3.2},
                'products': {'CSH': 1, 'CH': 1}
            },
            'C3A': {
                'reactants': {'C3A': 1, 'H2O': 6, 'CaSO4': 3},
                'products': {'ettringite': 1}
            },
            'C4AF': {
                'reactants': {'C4AF': 1, 'H2O': 6, 'CaSO4': 3},
                'products': {'ettringite': 1, 'Fe(OH)3': 2}
            }
        }
        
        # 计算每种矿物的水化热
        for mineral, reaction in reactions.items():
            try:
                delta_H = self.cemdata_reader.calculate_reaction_enthalpy(
                    reaction['reactants'], 
                    reaction['products']
                )
                if delta_H != 0:
                    # 转换为J/g
                    if mineral in self.molar_mass:
                        molar_mass = self.molar_mass[mineral]
                        hydration_heat_j_g = delta_H * 1000 / molar_mass  # 转换为J/g
                        self.hydration_heat[mineral] = hydration_heat_j_g
                        logger.info(f"Updated hydration heat for {mineral}: {hydration_heat_j_g:.2f} J/g")
            except Exception as e:
                logger.warning(f"Error updating hydration heat for {mineral}: {e}")
    
    def calculate_csh_composition(self, slag_mass=0, fly_ash_mass=0, cement_mass=100, temperature=20):
        """Calculate C-S-H composition based on slag and fly ash content and temperature"""
        try:
            # Calculate total binder mass
            total_binder = cement_mass + slag_mass + fly_ash_mass
            
            # Calculate replacement ratios
            slag_ratio = slag_mass / total_binder if total_binder > 0 else 0
            fly_ash_ratio = fly_ash_mass / total_binder if total_binder > 0 else 0
            
            # Base C-S-H composition for pure Portland cement
            # Adjust based on temperature - higher temperature leads to lower Ca/Si ratio
            temp_factor = 1 - 0.001 * (temperature - 20)  # Linear adjustment
            base_ca_si = 1.8 * temp_factor
            base_al_si = 0.1
            
            # Adjust C-S-H composition based on slag and fly ash content
            # Slag decreases Ca/Si ratio and increases Al/Si ratio
            # Fly ash also decreases Ca/Si ratio but more significantly
            ca_si_ratio = base_ca_si - 0.8 * slag_ratio - 0.6 * fly_ash_ratio
            al_si_ratio = base_al_si + 0.2 * slag_ratio + 0.15 * fly_ash_ratio
            
            # Ensure reasonable ratios
            ca_si_ratio = max(0.8, min(1.8, ca_si_ratio))
            al_si_ratio = max(0.05, min(0.5, al_si_ratio))
            
            # Determine which C-S-H model to use based on Ca/Si ratio
            if ca_si_ratio >= 1.5:
                csh_model = 'cshq'  # Q-phase C-S-H
            elif ca_si_ratio >= 1.2:
                csh_model = 'cshkn'  # Kato-Nishiyama C-S-H
            elif ca_si_ratio >= 1.0:
                csh_model = 'csh3t'  # 3T C-S-H
            else:
                csh_model = 'csh2o'  # 2O C-S-H
            
            # Get model parameters
            model_params = self.csh_models.get(csh_model, self.csh_models['cshq'])
            
            return {
                'ca_si_ratio': ca_si_ratio,
                'al_si_ratio': al_si_ratio,
                'csh_model': csh_model,
                'csh_name': model_params['name'],
                'density': model_params['density'],
                'molar_volume': model_params['molar_volume'],
                'h2o_si_ratio': model_params['h2o_si_ratio']
            }
        except Exception as e:
            print(f"Error calculating C-S-H composition: {e}")
            # Return default values
            return {
                'ca_si_ratio': 1.5,
                'al_si_ratio': 0.1,
                'csh_model': 'cshq',
                'csh_name': 'Q-phase C-S-H',
                'density': 2500,
                'molar_volume': 75,
                'h2o_si_ratio': 2.1
            }
    
    def calculate_slag_reactivity(self, time_days, temperature=20, w_c=0.5):
        """Calculate slag reactivity based on time, temperature, and water-cement ratio"""
        try:
            # Based on Kolani's model and experimental data
            # Base reactivity model
            base_reactivity = 0.34 * (1 - np.exp(-0.005 * time_days))
            
            # Temperature effect
            T_ref = 293.15  # 20°C in K
            T = 273.15 + temperature
            if T <= 0:
                return 0
            temp_factor = np.exp(-40000/8.314 * (1/T - 1/T_ref))
            base_reactivity *= temp_factor
            
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)
            base_reactivity *= water_factor
            
            # Limit maximum reactivity
            base_reactivity = min(base_reactivity, 0.34)
            base_reactivity = max(0, base_reactivity)
            
            return base_reactivity
        except Exception as e:
            print(f"Error calculating slag reactivity: {e}")
            return 0.0
    
    def calculate_fly_ash_reactivity(self, time_days, temperature=20, w_c=0.5):
        """Calculate fly ash reactivity based on time, temperature, and water-cement ratio"""
        try:
            # Based on experimental data and CEMDATA07
            # Base reactivity model
            base_reactivity = 0.25 * (1 - np.exp(-0.002 * time_days))
            
            # Temperature effect
            T_ref = 293.15  # 20°C in K
            T = 273.15 + temperature
            if T <= 0:
                return 0
            temp_factor = np.exp(-60000/8.314 * (1/T - 1/T_ref))
            base_reactivity *= temp_factor
            
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)
            base_reactivity *= water_factor
            
            # Limit maximum reactivity
            base_reactivity = min(base_reactivity, 0.25)
            base_reactivity = max(0, base_reactivity)
            
            return base_reactivity
        except Exception as e:
            print(f"Error calculating fly ash reactivity: {e}")
            return 0.0
    
    def calculate_hydration_products(self, cement_mass, hydration_degrees, fly_ash_mass=0, slag_mass=0, time_days=0, temperature=20, w_c=0.5):
        """Calculate hydration products"""
        raise NotImplementedError("Subclass must implement this method")
    
    def calculate_heat_generation(self, cement_mass, hydration_degrees):
        """Calculate heat generation during hydration"""
        try:
            heat = 0
            for mineral, degree in hydration_degrees.items():
                if mineral in self.hydration_heat:
                    heat += cement_mass * 1000 * self.clinker_composition.get(mineral, 0) * degree * abs(self.hydration_heat[mineral])
            return heat / 1000  # Convert to kJ
        except Exception as e:
            print(f"Error calculating heat generation: {e}")
            return 0.0
    
    def calculate_volume_change(self, cement_mass, hydration_degrees):
        """Calculate volume change during hydration"""
        try:
            # Calculate initial volume of cement minerals
            initial_volume = 0
            for mineral, fraction in self.clinker_composition.items():
                if mineral in self.molar_volume and mineral in self.molar_mass:
                    mass = cement_mass * fraction
                    moles = mass * 1000 / self.molar_mass[mineral]
                    initial_volume += moles * self.molar_volume[mineral]
            
            # Calculate final volume of hydration products (simplified)
            if initial_volume > 0:
                final_volume = initial_volume * 1.02  # Assume 2% volume increase
                return (final_volume - initial_volume) / initial_volume
            else:
                return 0  # Avoid division by zero
        except Exception as e:
            print(f"Error calculating volume change: {e}")
            return 0.0
    
    def calculate_adiabatic_temperature(self, mix_design, time_days_list, initial_temperature=20, mode='adiabatic'):
        """Calculate adiabatic or semi-adiabatic temperature rise"""
        try:
            # Calculate total mass of concrete
            total_mass = sum(mix_design.values())
            
            # Calculate effective specific heat capacity
            total_specific_heat = 0
            for material, mass in mix_design.items():
                if material in self.specific_heat:
                    total_specific_heat += mass * self.specific_heat[material]
            effective_cp = total_specific_heat / total_mass if total_mass > 0 else 900
            
            # Calculate water-cement ratio
            w_c = self.calculate_water_cement_ratio(mix_design)
            
            # Extract nano materials and chemical admixtures
            nano_materials = {}
            nano_keys = ['Nano SiO2', 'Nano Al2O3', 'Nano CaCO3', 'Nano CaO', 'Nano MgO', 'Graphene']
            for key in nano_keys:
                if key in mix_design and mix_design[key] > 0:
                    nano_materials[key] = mix_design[key]
            
            chemical_admixtures = {}
            chemical_keys = ['CaCl2', 'AlCl3', 'Na2SO4', 'NaOH', 'KOH', 'Na2CO3', 'K2CO3', 'Retarder', 'Superplasticizer']
            for key in chemical_keys:
                if key in mix_design and mix_design[key] > 0:
                    chemical_admixtures[key] = mix_design[key]
            
            # Calculate heat generation and temperature rise
            temperature_rises = []
            temperatures = []
            current_temperature = initial_temperature
            previous_heat = 0
            
            for i, time_days in enumerate(time_days_list):
                # Calculate hydration degrees
                degrees = self.calculate_hydration_degree(time_days, current_temperature, w_c, nano_materials, chemical_admixtures)
                
                # Calculate heat generation
                cement_mass = mix_design.get('Cement', 0)
                current_heat = self.calculate_heat_generation(cement_mass, degrees)
                
                # Calculate heat increment (only for time steps after the first)
                if i == 0:
                    heat_increment = current_heat
                else:
                    heat_increment = current_heat - previous_heat
                
                # Calculate temperature rise
                if total_mass > 0 and effective_cp > 0:
                    temperature_rise = heat_increment / (total_mass * effective_cp / 1000)  # Convert cp to kJ/(kg·°C)
                else:
                    temperature_rise = 0
                
                if mode == 'semi-adiabatic':
                    # For semi-adiabatic, assume some heat loss
                    heat_loss_factor = 0.8  # 20% heat loss
                    temperature_rise *= heat_loss_factor
                
                current_temperature += temperature_rise
                temperature_rises.append(temperature_rise)
                temperatures.append(current_temperature)
                previous_heat = current_heat
            
            return temperature_rises, temperatures
        except Exception as e:
            print(f"Error calculating adiabatic temperature: {e}")
            # Return empty lists if error occurs
            return [], []
    
    def calculate_strength(self, time_days):
        """Calculate concrete strength development"""
        raise NotImplementedError("Subclass must implement this method")
    
    def simulate_hydration(self, mix_design, time_days_list, temperature=20, use_gems3k=True):
        """Simulate hydration process"""
        results = {
            'time_days': time_days_list,
            'hydration_degrees': [],
            'hydration_products': [],
            'heat_generation': [],
            'volume_change': [],
            'strength': []
        }
        
        # Add GEMS3K-specific results if enabled
        if use_gems3k:
            results['thermodynamic_data'] = []
            results['equilibrium_constants'] = []
            results['saturation_indices'] = []
        
        w_c = self.calculate_water_cement_ratio(mix_design)
        cement_mass = mix_design.get('Cement', 0)
        fly_ash_mass = mix_design.get('Fly Ash', 0)
        slag_mass = mix_design.get('Slag', 0)
        
        for time_days in time_days_list:
            # Calculate hydration degrees
            degrees = self.calculate_hydration_degree(time_days, temperature, w_c)
            results['hydration_degrees'].append(degrees)
            
            # Calculate hydration products
            products = self.calculate_hydration_products(cement_mass, degrees, fly_ash_mass, slag_mass, time_days, temperature, w_c)
            results['hydration_products'].append(products)
            
            # Calculate heat generation
            heat = self.calculate_heat_generation(cement_mass, degrees)
            results['heat_generation'].append(heat)
            
            # Calculate volume change
            volume_change = self.calculate_volume_change(cement_mass, degrees)
            results['volume_change'].append(volume_change)
            
            # Calculate strength
            strength = self.calculate_strength(time_days)
            results['strength'].append(strength)
            
            # Add GEMS3K-enhanced data if enabled
            if use_gems3k:
                enhanced_results = self.enhance_hydration_calculation(mix_design, time_days, temperature)
                results['thermodynamic_data'].append(enhanced_results['thermodynamic_data'])
                results['equilibrium_constants'].append(enhanced_results['equilibrium_constants'])
                results['saturation_indices'].append(enhanced_results['saturation_indices'])
        
        return results
    
    def calculate_chloride_diffusion(self, depth_mm, concentration, time_days):
        """Calculate chloride diffusion coefficient"""
        diffusion = ChlorideDiffusion()
        results = diffusion.calculate_diffusion_coefficient(depth_mm, concentration, time_days)
        if results:
            diffusion.plot_concentration_profile(depth_mm, concentration, results)
        return results
    
    def predict_strength_ml(self, inputs=None):
        """Predict concrete strength using machine learning"""
        predictor = MLStrengthPrediction()
        if inputs is None:
            inputs = predictor.get_default_inputs()
        results = predictor.predict_strength(inputs)
        return results
    
    def enhance_hydration_calculation(self, mix_design, time_days, temperature=20):
        """Enhance hydration calculation using GEMS3K
        
        Args:
            mix_design: Mix design dictionary
            time_days: Hydration time in days
            temperature: Temperature in °C
            
        Returns:
            dict: Enhanced hydration results
        """
        return self.gems3k_enhancer.enhance_hydration_calculation(self, mix_design, time_days, temperature)
    
    def optimize_mix_design(self, base_mix_design, target_strength, temperature=20):
        """Optimize mix design using GEMS3K thermodynamic data
        
        Args:
            base_mix_design: Base mix design dictionary
            target_strength: Target compressive strength in MPa
            temperature: Temperature in °C
            
        Returns:
            dict: Optimized mix design
        """
        return self.gems3k_enhancer.optimize_mix_design(self, base_mix_design, target_strength, temperature)
    
    def get_thermodynamic_data(self, component_name, pressure=1e5, temperature=298.15):
        """Get thermodynamic data for a component using GEMS3K
        
        Args:
            component_name: Component name
            pressure: Pressure in Pa
            temperature: Temperature in K
            
        Returns:
            dict: Thermodynamic data
        """
        return self.gems3k_interface.get_thermodynamic_data(component_name, pressure, temperature)
    
    def calculate_reaction_enthalpy(self, reactants, products, pressure=1e5, temperature=298.15):
        """Calculate reaction enthalpy using GEMS3K
        
        Args:
            reactants: Dict of reactants {component: moles}
            products: Dict of products {component: moles}
            pressure: Pressure in Pa
            temperature: Temperature in K
            
        Returns:
            float: Reaction enthalpy in J/mol
        """
        return self.gems3k_interface.calculate_reaction_enthalpy(reactants, products, pressure, temperature)
    
    def calculate_equilibrium_constant(self, reactants, products, pressure=1e5, temperature=298.15):
        """Calculate equilibrium constant using GEMS3K
        
        Args:
            reactants: Dict of reactants {component: moles}
            products: Dict of products {component: moles}
            pressure: Pressure in Pa
            temperature: Temperature in K
            
        Returns:
            float: Equilibrium constant
        """
        return self.gems3k_interface.calculate_equilibrium_constant(reactants, products, pressure, temperature)
    
    def calculate_saturation_index(self, mineral, ions, temperature=25):
        """Calculate saturation index for a mineral using GEMS3K
        
        Args:
            mineral: Mineral name
            ions: Dict of ion concentrations {ion: concentration in mol/L}
            temperature: Temperature in °C
            
        Returns:
            float: Saturation index
        """
        return self.gems3k_interface.calculate_saturation_index(mineral, ions, temperature)
    
    def calculate_activity_coefficient(self, ion, concentration, temperature=25):
        """Calculate activity coefficient for an ion using GEMS3K
        
        Args:
            ion: Ion name
            concentration: Ion concentration in mol/L
            temperature: Temperature in °C
            
        Returns:
            float: Activity coefficient
        """
        return self.gems3k_interface.calculate_activity_coefficient(ion, concentration, temperature)
    
    def close_gems3k(self):
        """Close GEMS3K and free resources"""
        self.gems3k_interface.close()
    
    def enhance_mix_design(self, mix_design, target_strength, target_workability='self-compacting'):
        """Enhance mix design using EMMA
        
        Args:
            mix_design: Mix design dictionary
            target_strength: Target compressive strength in MPa
            target_workability: Target workability ('self-compacting', 'vibratable', 'flowing')
            
        Returns:
            dict: Enhanced mix design
        """
        return self.emma_enhancer.enhance_mix_design(mix_design, target_strength, target_workability)
    
    def optimize_particle_packing(self, materials, target_q=0.28, max_particle_size=8000):
        """Optimize particle packing using Andreassen model
        
        Args:
            materials: Dict of materials and their weights {material_name: weight}
            target_q: Target q-value
            max_particle_size: Maximum particle size in microns
            
        Returns:
            dict: Optimization results
        """
        return self.emma_interface.optimize_particle_packing(materials, target_q, max_particle_size)
    
    def calculate_co2_impact(self, materials):
        """Calculate CO2 impact of a mix
        
        Args:
            materials: Dict of materials and their weights {material_name: weight}
            
        Returns:
            float: Total CO2 impact
        """
        return self.emma_interface.calculate_co2_impact(materials)
    
    def estimate_density(self, materials):
        """Estimate density of a mix
        
        Args:
            materials: Dict of materials and their weights {material_name: weight}
            
        Returns:
            float: Estimated density
        """
        return self.emma_interface.estimate_density(materials)
    
    def optimize_mix_for_strength(self, base_mix, target_strength):
        """Optimize mix for target strength
        
        Args:
            base_mix: Base mix design
            target_strength: Target strength in MPa
            
        Returns:
            dict: Optimized mix
        """
        return self.emma_enhancer.optimize_mix_for_strength(base_mix, target_strength)
    
    def reduce_co2_impact(self, mix_design, reduction_target=0.1):
        """Reduce CO2 impact of a mix
        
        Args:
            mix_design: Mix design dictionary
            reduction_target: Target reduction in CO2 impact (fraction)
            
        Returns:
            dict: CO2-reduced mix design
        """
        return self.emma_enhancer.reduce_co2_impact(mix_design, reduction_target)
    
    def list_emma_materials(self):
        """List all EMMA materials
        
        Returns:
            list: List of material names
        """
        return self.emma_interface.list_materials()
    
    def get_emma_material(self, material_name):
        """Get EMMA material by name
        
        Args:
            material_name: Material name
            
        Returns:
            dict: Material data
        """
        return self.emma_interface.get_material(material_name)
    
    def plot_particle_size_distribution(self, optimization_results, title="Particle Size Distribution"):
        """Plot particle size distribution
        
        Args:
            optimization_results: Optimization results from optimize_particle_packing
            title: Plot title
        """
        self.emma_interface.plot_particle_size_distribution(optimization_results, title)
