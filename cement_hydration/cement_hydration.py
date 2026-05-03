#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cement Hydration Simulation
Based on Cemdata18 database and example mix design
"""

import numpy as np
# matplotlib is optional for hydration simulation
try:
    import matplotlib.pyplot as plt
except ImportError:
    pass

class CementHydration:
    def __init__(self, cement_type='portland', cement_ratio=None):
        """Initialize cement hydration simulator
        
        Args:
            cement_type: Type of cement ('portland', 'sulphoaluminate', 'aluminate', 'magnesium_phosphate', 'portland_sulphoaluminate', or 'portland_sulphoaluminate_gypsum')
            cement_ratio: Dictionary of cement ratios for composite systems (e.g., {'portland': 0.5, 'sulphoaluminate': 0.5} for 50:50 blend)
        """
        # Cement type
        self.cement_type = cement_type
        
        # Cement ratio for composite systems
        self.cement_ratio = cement_ratio if cement_ratio else {}
        
        # Cement clinker mineral composition (mass fraction)
        if cement_type == 'portland':
            # Portland cement
            self.clinker_composition = {
                'C3S': 0.65,   # Tricalcium silicate
                'C2S': 0.15,   # Dicalcium silicate
                'C3A': 0.10,   # Tricalcium aluminate
                'C4AF': 0.10   # Tetracalcium aluminoferrite
            }
        elif cement_type == 'sulphoaluminate':
            # Sulphoaluminate cement
            self.clinker_composition = {
                'C4A3S': 0.50,  # Tricalcium sulfoaluminate
                'C2S': 0.25,    # Dicalcium silicate
                'C4AF': 0.10,   # Tetracalcium aluminoferrite
                'CaSO4': 0.15   # Gypsum
            }
        elif cement_type == 'aluminate':
            # Aluminate cement
            self.clinker_composition = {
                'CA': 0.40,     # Monocalcium aluminate
                'CA2': 0.35,    # Dicalcium aluminate
                'C12A7': 0.15,  # Calcium aluminate (12CaO·7Al2O3)
                'C2S': 0.10     # Dicalcium silicate
            }
        elif cement_type == 'magnesium_phosphate':
            # Magnesium phosphate cement
            self.clinker_composition = {
                'MgO': 0.60,    # Magnesium oxide
                'KH2PO4': 0.40  # Potassium dihydrogen phosphate (MKP)
            }
        elif cement_type == 'portland_sulphoaluminate':
            # Portland + Sulphoaluminate cement blend
            # Default ratio: 50:50
            portland_ratio = self.cement_ratio.get('portland', 0.5)
            sulphoaluminate_ratio = self.cement_ratio.get('sulphoaluminate', 0.5)
            
            # Calculate composite composition
            self.clinker_composition = {
                'C3S': 0.65 * portland_ratio,
                'C2S': 0.15 * portland_ratio + 0.25 * sulphoaluminate_ratio,
                'C3A': 0.10 * portland_ratio,
                'C4AF': 0.10 * portland_ratio + 0.10 * sulphoaluminate_ratio,
                'C4A3S': 0.50 * sulphoaluminate_ratio,
                'CaSO4': 0.15 * sulphoaluminate_ratio
            }
        elif cement_type == 'portland_sulphoaluminate_gypsum':
            # Portland + Sulphoaluminate + Gypsum blend
            # Default ratio: 40:40:20
            portland_ratio = self.cement_ratio.get('portland', 0.4)
            sulphoaluminate_ratio = self.cement_ratio.get('sulphoaluminate', 0.4)
            gypsum_ratio = self.cement_ratio.get('gypsum', 0.2)
            
            # Calculate composite composition
            self.clinker_composition = {
                'C3S': 0.65 * portland_ratio,
                'C2S': 0.15 * portland_ratio + 0.25 * sulphoaluminate_ratio,
                'C3A': 0.10 * portland_ratio,
                'C4AF': 0.10 * portland_ratio + 0.10 * sulphoaluminate_ratio,
                'C4A3S': 0.50 * sulphoaluminate_ratio,
                'CaSO4': 0.15 * sulphoaluminate_ratio + 1.0 * gypsum_ratio
            }
        
        # Density (kg/m³)
        self.densities = {
            'Water': 1000,
            'Cement': 3150,
            'Fly Ash': 2400,
            'Slag': 2900,      # Ground granulated blast furnace slag
            'Silica Fume': 2200,  # Silica fume
            'Kaolin': 2600,    # Calcined kaolin
            'CSH Seed': 2500,  # CSH seed
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
            'Concrete': 2400  # Average concrete density
        }
        
        # Specific heat capacity (J/(kg·°C))
        self.specific_heat = {
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
            'Concrete': 900  # Average concrete specific heat
        }
        
        # Nano materials effect on hydration
        self.nano_effects = {
            'Nano SiO2': {
                'hydration_acceleration': 1.5,  # Accelerates hydration rate
                'cs_h_nucleation': 2.0,        # Enhances CSH nucleation
                'pozzolanic_reactivity': 1.8,   # Pozzolanic reaction
                'strength_enhancement': 1.3     # Strength improvement factor
            },
            'Nano Al2O3': {
                'hydration_acceleration': 1.3,  # Accelerates hydration rate
                'afm_formation': 1.5,          # Enhances AFm formation
                'strength_enhancement': 1.2     # Strength improvement factor
            },
            'Nano CaCO3': {
                'hydration_acceleration': 1.2,  # Accelerates hydration rate
                'csh_seed_effect': 1.6,        # CSH seed effect
                'strength_enhancement': 1.1     # Strength improvement factor
            },
            'Nano CaO': {
                'hydration_acceleration': 1.8,  # Strongly accelerates hydration
                'alkaline_enhancement': 2.0,    # Increases alkalinity
                'strength_enhancement': 1.4     # Strength improvement factor
            },
            'Nano MgO': {
                'hydration_acceleration': 1.1,  # Slightly accelerates hydration
                'expansion_control': 1.3,       # Controls shrinkage
                'strength_enhancement': 1.05    # Slight strength improvement
            },
            'Graphene': {
                'hydration_acceleration': 1.4,  # Accelerates hydration
                'nucleation_sites': 2.2,        # Provides nucleation sites
                'strength_enhancement': 1.5,    # Significant strength improvement
                'conductivity_enhancement': 10.0  # Enhances conductivity
            }
        }
        
        # Default mix design values (kg/m³)
        self.default_mix_design = {
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
            # Chemical admixtures
            'CaCl2': 0,           # Accelerator
            'AlCl3': 0,           # Accelerator
            'Na2SO4': 0,          # Accelerator
            'NaOH': 0,            # Accelerator/Alkaline activator
            'KOH': 0,             # Accelerator/Alkaline activator
            'Na2CO3': 0,          # Accelerator
            'K2CO3': 0,           # Accelerator
            'Retarder': 0,         # Retarder (e.g., sucrose, citric acid)
            'Superplasticizer': 0,  # Water reducer
            'AirEntrainer': 0,     # Air entrainer
            'ViscosityModifier': 0 # Viscosity modifier
        }
        
        # Chemical admixtures effect on hydration
        self.chemical_admixtures_effects = {
            'CaCl2': {
                'hydration_acceleration': 1.8,  # Strong acceleration
                'c3a_acceleration': 2.5,       # Strongly accelerates C3A
                'freezing_point_reduction': 1.5  # Reduces freezing point
            },
            'AlCl3': {
                'hydration_acceleration': 1.6,  # Strong acceleration
                'c3a_acceleration': 2.0,       # Accelerates C3A
                'setting_acceleration': 1.8     # Accelerates setting
            },
            'Na2SO4': {
                'hydration_acceleration': 1.4,  # Moderate acceleration
                'c3a_modification': 1.2,       # Modifies C3A reaction
                'sulfate_activation': 1.5       # Provides sulfate ions
            },
            'NaOH': {
                'hydration_acceleration': 1.5,  # Moderate acceleration
                'alkaline_enhancement': 2.5,   # Strongly increases alkalinity
                'silicate_dissolution': 1.8     # Enhances silicate dissolution
            },
            'KOH': {
                'hydration_acceleration': 1.5,  # Moderate acceleration
                'alkaline_enhancement': 2.5,   # Strongly increases alkalinity
                'silicate_dissolution': 1.8     # Enhances silicate dissolution
            },
            'Na2CO3': {
                'hydration_acceleration': 1.3,  # Mild acceleration
                'alkaline_enhancement': 1.8,   # Increases alkalinity
                'carbonation_effect': 1.2       # May cause carbonation
            },
            'K2CO3': {
                'hydration_acceleration': 1.3,  # Mild acceleration
                'alkaline_enhancement': 1.8,   # Increases alkalinity
                'carbonation_effect': 1.2       # May cause carbonation
            },
            'Retarder': {
                'hydration_retardation': 0.6,   # Slows hydration
                'setting_retardation': 0.5,     # Delays setting
                'workability_improvement': 1.3  # Improves workability
            },
            'Superplasticizer': {
                'water_reduction': 0.8,         # Reduces water demand
                'workability_improvement': 1.5,  # Improves workability
                'dispersion_effect': 1.2        # Disperses cement particles
            },
            'AirEntrainer': {
                'air_content_increase': 1.5,    # Increases air content
                'workability_improvement': 1.2,  # Improves workability
                'freezing_thawing_resistance': 1.3  # Improves F-T resistance
            },
            'ViscosityModifier': {
                'viscosity_increase': 1.5,      # Increases viscosity
                'segregation_reduction': 1.3,   # Reduces segregation
                'bleeding_reduction': 1.4       # Reduces bleeding
            }
        }
        
        # Molar mass (g/mol)
        self.molar_mass = {
            'C3S': 228.31,     # Ca3SiO5
            'C2S': 172.27,     # Ca2SiO4
            'C3A': 270.21,     # Ca3Al2O6
            'C4AF': 485.97,    # Ca4Al2Fe2O10
            'C4A3S': 466.23,   # Ca4Al6SO16 (Tricalcium sulfoaluminate)
            'CaSO4': 136.14,   # Calcium sulfate (Gypsum)
            'CA': 158.04,      # CaAl2O4 (Monocalcium aluminate)
            'CA2': 222.15,     # CaAl4O7 (Dicalcium aluminate)
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
        
        # Molar volume (cm³/mol) from CEMDATA07
        self.molar_volume = {
            'C3S': 73,           # Tricalcium silicate
            'C2S': 52,           # Dicalcium silicate
            'C3A': 89,           # Tricalcium aluminate
            'C4AF': 130,         # Tetracalcium aluminoferrite
            'C4A3S': 145,         # Tricalcium sulfoaluminate
            'CaSO4': 46.9,        # Calcium sulfate (Gypsum)
            'CA': 52.5,          # Monocalcium aluminate
            'CA2': 68.0,         # Dicalcium aluminate
            'C12A7': 350.0,      # 12CaO·7Al2O3
            'MgO': 11.25,         # Magnesium oxide
            'KH2PO4': 74.0,       # Potassium dihydrogen phosphate (MKP)
            'CSH': 78.4,         # Jennite-type C-S-H
            'CH': 33.06,         # Portlandite
            'AFt': 707,          # Ettringite
            'AFm': 310.1,        # Monosulphate12
            'H2O': 18.068,       # Water
            'ettringite': 707,    # Ettringite
            'monosulphate': 310.1, # Monosulphate12
            'tricarboaluminate': 650, # Tricarboaluminate
            'C3AH6': 150,        # C3AH6
            'C4AH13': 274,       # C4AH13
            'C2AH8': 184,        # C2AH8
            'straetlingite': 216,  # Straetlingite
            'thaumasite': 650,    # Thaumasite
            'ettringite_sulpho': 707, # Ettringite from sulphoaluminate hydration
            'CAH10': 220,        # CaAl2(OH)8·6H2O
            'AH3': 31.96,         # Al(OH)3 (Gibbsite)
            'MCPM': 180.0,       # MgKHPO4·6H2O (Monocalcium phosphate monohydrate)
            'MKP': 74.0,          # KH2PO4 (Potassium dihydrogen phosphate)
            'MgO': 11.25         # Magnesium oxide
        }
        
        # Hydration heat (J/g) based on CEMDATA07
        # Calculated from ΔfH° values
        self.hydration_heat = {
            'C3S': -502,    # Heat of hydration for C3S (J/g)
            'C2S': -260,    # Heat of hydration for C2S (J/g)
            'C3A': -946,    # Heat of hydration for C3A (J/g)
            'C4AF': -418,   # Heat of hydration for C4AF (J/g)
            'C4A3S': -1100, # Heat of hydration for C4A3S (J/g) - higher than C3A
            'CaSO4': -150,  # Heat of hydration for CaSO4 (J/g)
            'CA': -1000,    # Heat of hydration for CA (J/g) - high heat release
            'CA2': -800,    # Heat of hydration for CA2 (J/g)
            'C12A7': -900,  # Heat of hydration for C12A7 (J/g)
            'MgO': -800,     # Heat of hydration for MgO (J/g) - high heat release
            'KH2PO4': -600  # Heat of hydration for KH2PO4 (J/g)
        }
        
        # Thermodynamic data from CEMDATA07
        self.thermodynamic_data = {
            'C3S': {'delta_fH': -2931, 'S': 209},     # kJ/mol, J/K/mol
            'C2S': {'delta_fH': -2308, 'S': 152},     # kJ/mol, J/K/mol
            'C3A': {'delta_fH': -3561, 'S': 261},     # kJ/mol, J/K/mol
            'C4AF': {'delta_fH': -5080, 'S': 374},    # kJ/mol, J/K/mol
            'CH': {'delta_fH': -986, 'S': 83},         # kJ/mol, J/K/mol
            'ettringite': {'delta_fH': -17535, 'S': 1939}, # kJ/mol, J/K/mol
            'monosulphate': {'delta_fH': -8750, 'S': 594}, # kJ/mol, J/K/mol
            'C3AH6': {'delta_fH': -5540, 'S': 292},    # kJ/mol, J/K/mol
            'C4AH13': {'delta_fH': -8302, 'S': 711},   # kJ/mol, J/K/mol
            'CSH': {'delta_fH': -2723, 'S': 210}       # kJ/mol, J/K/mol (Jennite-type)
        }
        
    def calculate_water_cement_ratio(self, mix_design):
        """Calculate water-cement ratio"""
        water = mix_design.get('Water', 0)
        cement = mix_design.get('Cement', 0)
        return water / cement if cement > 0 else 0
    
    def calculate_hydration_degree(self, time_days, temperature=20, w_c=0.5, nano_materials=None, chemical_admixtures=None):
        """Calculate hydration degree of different minerals based on CEMDATA18 kinetics
        
        Args:
            time_days: Time in days
            temperature: Temperature in °C (default: 20°C)
            w_c: Water-cement ratio (default: 0.5)
            nano_materials: Dictionary of nano materials and their mass fractions (default: None)
            chemical_admixtures: Dictionary of chemical admixtures and their mass fractions (default: None)
        """
        degrees = {}
        
        # Temperature factor (Arrhenius equation) - based on CEMDATA18 activation energies
        if self.cement_type == 'portland':
            Ea = {
                'C3S': 30000,  # Activation energy in J/mol
                'C2S': 40000,
                'C3A': 25000,
                'C4AF': 28000
            }
        elif self.cement_type == 'sulphoaluminate':
            Ea = {
                'C4A3S': 20000,  # Lower activation energy than C3A
                'C2S': 40000,
                'C4AF': 28000,
                'CaSO4': 15000   # Lower activation energy for gypsum
            }
        elif self.cement_type == 'aluminate':
            Ea = {
                'CA': 18000,     # Lower activation energy for faster hydration
                'CA2': 22000,    # Slightly higher activation energy
                'C12A7': 20000,  # Moderate activation energy
                'C2S': 40000     # Same as portland cement
            }
        elif self.cement_type == 'magnesium_phosphate':
            Ea = {
                'MgO': 15000,     # Lower activation energy for very fast hydration
                'KH2PO4': 12000   # Very low activation energy for rapid dissolution
            }
        elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
            # Composite cement systems - include all relevant minerals
            Ea = {
                'C3S': 30000,
                'C2S': 40000,
                'C3A': 25000,
                'C4AF': 28000,
                'C4A3S': 20000,
                'CaSO4': 15000
            }
        
        R = 8.314  # Gas constant in J/(mol·K)
        T_ref = 293.15  # Reference temperature (20°C) in K
        T = 273.15 + temperature  # Current temperature in K
        
        # Water availability factor - more realistic water consumption effect
        water_factor = min(1.0, w_c / 0.45)  # Assume 0.45 is minimum w/c for full hydration
        
        # Calculate nano materials effect factor
        nano_factor = 1.0
        if nano_materials:
            for nano, mass in nano_materials.items():
                if nano in self.nano_effects and mass > 0:
                    # Calculate effect based on mass fraction (assuming total binder mass)
                    effect = self.nano_effects[nano].get('hydration_acceleration', 1.0)
                    nano_factor *= effect ** (mass / 10)  # Normalize by 10kg/m³
        
        # Limit nano factor to avoid unrealistic acceleration
        nano_factor = min(nano_factor, 2.5)
        
        # Calculate chemical admixtures effect factors
        chemical_factor = 1.0
        c3a_factor = 1.0
        
        if chemical_admixtures:
            for admixture, mass in chemical_admixtures.items():
                if admixture in self.chemical_admixtures_effects and mass > 0:
                    effects = self.chemical_admixtures_effects[admixture]
                    
                    # Hydration acceleration/retardation
                    if 'hydration_acceleration' in effects:
                        chemical_factor *= effects['hydration_acceleration'] ** (mass / 1)
                    if 'hydration_retardation' in effects:
                        chemical_factor *= effects['hydration_retardation'] ** (mass / 0.1)
                    
                    # C3A specific effects (also applies to C4A3S in sulphoaluminate cement)
                    if 'c3a_acceleration' in effects:
                        c3a_factor *= effects['c3a_acceleration'] ** (mass / 1)
                    if 'c3a_modification' in effects:
                        c3a_factor *= effects['c3a_modification'] ** (mass / 1)
        
        # Limit chemical factors to avoid unrealistic effects
        chemical_factor = min(chemical_factor, 3.0)  # Maximum acceleration
        chemical_factor = max(chemical_factor, 0.3)  # Maximum retardation
        c3a_factor = min(c3a_factor, 3.0)  # Maximum C3A/C4A3S acceleration

        if self.cement_type == 'portland':
            # C3S hydration kinetics - three-stage model based on CEMDATA18
            temp_factor_c3s = np.exp(-Ea['C3S']/R * (1/T - 1/T_ref))
            if time_days < 1:
                # Initial stage - rapid dissolution
                alpha_c3s = 1 - np.exp(-5.0 * temp_factor_c3s * nano_factor * chemical_factor * time_days)
            elif time_days < 14:
                # Accelerating stage - CSH nucleation and growth
                alpha_c3s = 0.3 + 0.4 * (1 - np.exp(-0.8 * temp_factor_c3s * nano_factor * chemical_factor * (time_days - 1)))
            else:
                # Decelerating stage - diffusion controlled
                alpha_c3s = 0.7 + 0.2 * (1 - np.exp(-0.1 * temp_factor_c3s * nano_factor * chemical_factor * (time_days - 14)))
            degrees['C3S'] = min(alpha_c3s * water_factor, 0.95)  # Maximum hydration degree 95%
            
            # C2S hydration kinetics - slower, more gradual
            temp_factor_c2s = np.exp(-Ea['C2S']/R * (1/T - 1/T_ref))
            alpha_c2s = 1 - np.exp(-0.3 * temp_factor_c2s * nano_factor * chemical_factor * time_days**0.7)
            degrees['C2S'] = min(alpha_c2s * water_factor, 0.85)  # Maximum hydration degree 85%
            
            # C3A hydration kinetics - very fast initial, then slows
            temp_factor_c3a = np.exp(-Ea['C3A']/R * (1/T - 1/T_ref))
            if time_days < 0.5:
                # Rapid initial hydration
                alpha_c3a = 1 - np.exp(-15.0 * temp_factor_c3a * nano_factor * chemical_factor * c3a_factor * time_days)
            else:
                # Slower hydration after initial
                alpha_c3a = 0.6 + 0.3 * (1 - np.exp(-0.3 * temp_factor_c3a * nano_factor * chemical_factor * c3a_factor * (time_days - 0.5)))
            degrees['C3A'] = min(alpha_c3a * water_factor, 0.98)  # Maximum hydration degree 98%
            
            # C4AF hydration kinetics
            temp_factor_c4af = np.exp(-Ea['C4AF']/R * (1/T - 1/T_ref))
            if time_days < 1:
                # Initial hydration
                alpha_c4af = 1 - np.exp(-4.0 * temp_factor_c4af * nano_factor * chemical_factor * time_days)
            else:
                # Slower hydration
                alpha_c4af = 0.4 + 0.4 * (1 - np.exp(-0.4 * temp_factor_c4af * nano_factor * chemical_factor * (time_days - 1)))
            degrees['C4AF'] = min(alpha_c4af * water_factor, 0.90)  # Maximum hydration degree 90%
        elif self.cement_type == 'sulphoaluminate':
            # C4A3S hydration kinetics - very fast, characteristic of sulphoaluminate cement
            temp_factor_c4a3s = np.exp(-Ea['C4A3S']/R * (1/T - 1/T_ref))
            if time_days < 0.2:
                # Initial stage - extremely rapid
                alpha_c4a3s = 1 - np.exp(-30.0 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * time_days)
            elif time_days < 1:
                # Accelerating stage
                alpha_c4a3s = 0.7 + 0.2 * (1 - np.exp(-5.0 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * (time_days - 0.2)))
            else:
                # Decelerating stage
                alpha_c4a3s = 0.9 + 0.1 * (1 - np.exp(-0.5 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * (time_days - 1)))
            degrees['C4A3S'] = min(alpha_c4a3s * water_factor, 0.99)  # Maximum hydration degree 99%
            
            # C2S hydration kinetics - similar to portland cement but slower relative to C4A3S
            temp_factor_c2s = np.exp(-Ea['C2S']/R * (1/T - 1/T_ref))
            alpha_c2s = 1 - np.exp(-0.2 * temp_factor_c2s * nano_factor * chemical_factor * time_days**0.7)
            degrees['C2S'] = min(alpha_c2s * water_factor, 0.80)  # Maximum hydration degree 80%
            
            # C4AF hydration kinetics - similar to portland cement
            temp_factor_c4af = np.exp(-Ea['C4AF']/R * (1/T - 1/T_ref))
            if time_days < 1:
                # Initial hydration
                alpha_c4af = 1 - np.exp(-3.0 * temp_factor_c4af * nano_factor * chemical_factor * time_days)
            else:
                # Slower hydration
                alpha_c4af = 0.4 + 0.3 * (1 - np.exp(-0.3 * temp_factor_c4af * nano_factor * chemical_factor * (time_days - 1)))
            degrees['C4AF'] = min(alpha_c4af * water_factor, 0.85)  # Maximum hydration degree 85%
            
            # CaSO4 hydration kinetics - rapid
            temp_factor_caso4 = np.exp(-Ea['CaSO4']/R * (1/T - 1/T_ref))
            alpha_caso4 = 1 - np.exp(-20.0 * temp_factor_caso4 * nano_factor * chemical_factor * time_days)
            degrees['CaSO4'] = min(alpha_caso4 * water_factor, 0.99)  # Maximum hydration degree 99%
        elif self.cement_type == 'aluminate':
            # CA hydration kinetics - very fast, characteristic of aluminate cement
            temp_factor_ca = np.exp(-Ea['CA']/R * (1/T - 1/T_ref))
            if time_days < 0.1:
                # Initial stage - extremely rapid
                alpha_ca = 1 - np.exp(-40.0 * temp_factor_ca * nano_factor * chemical_factor * c3a_factor * time_days)
            elif time_days < 0.5:
                # Accelerating stage
                alpha_ca = 0.8 + 0.15 * (1 - np.exp(-10.0 * temp_factor_ca * nano_factor * chemical_factor * c3a_factor * (time_days - 0.1)))
            else:
                # Decelerating stage
                alpha_ca = 0.95 + 0.05 * (1 - np.exp(-1.0 * temp_factor_ca * nano_factor * chemical_factor * c3a_factor * (time_days - 0.5)))
            degrees['CA'] = min(alpha_ca * water_factor, 0.99)  # Maximum hydration degree 99%
            
            # CA2 hydration kinetics - fast but slower than CA
            temp_factor_ca2 = np.exp(-Ea['CA2']/R * (1/T - 1/T_ref))
            if time_days < 0.2:
                # Initial hydration
                alpha_ca2 = 1 - np.exp(-20.0 * temp_factor_ca2 * nano_factor * chemical_factor * time_days)
            elif time_days < 1:
                # Accelerating stage
                alpha_ca2 = 0.6 + 0.3 * (1 - np.exp(-5.0 * temp_factor_ca2 * nano_factor * chemical_factor * (time_days - 0.2)))
            else:
                # Decelerating stage
                alpha_ca2 = 0.9 + 0.1 * (1 - np.exp(-0.5 * temp_factor_ca2 * nano_factor * chemical_factor * (time_days - 1)))
            degrees['CA2'] = min(alpha_ca2 * water_factor, 0.98)  # Maximum hydration degree 98%
            
            # C12A7 hydration kinetics - moderate speed
            temp_factor_c12a7 = np.exp(-Ea['C12A7']/R * (1/T - 1/T_ref))
            if time_days < 0.5:
                # Initial hydration
                alpha_c12a7 = 1 - np.exp(-10.0 * temp_factor_c12a7 * nano_factor * chemical_factor * time_days)
            elif time_days < 3:
                # Accelerating stage
                alpha_c12a7 = 0.5 + 0.4 * (1 - np.exp(-2.0 * temp_factor_c12a7 * nano_factor * chemical_factor * (time_days - 0.5)))
            else:
                # Decelerating stage
                alpha_c12a7 = 0.9 + 0.1 * (1 - np.exp(-0.3 * temp_factor_c12a7 * nano_factor * chemical_factor * (time_days - 3)))
            degrees['C12A7'] = min(alpha_c12a7 * water_factor, 0.97)  # Maximum hydration degree 97%
            
            # C2S hydration kinetics - similar to portland cement
            temp_factor_c2s = np.exp(-Ea['C2S']/R * (1/T - 1/T_ref))
            alpha_c2s = 1 - np.exp(-0.2 * temp_factor_c2s * nano_factor * chemical_factor * time_days**0.7)
            degrees['C2S'] = min(alpha_c2s * water_factor, 0.80)  # Maximum hydration degree 80%
        elif self.cement_type == 'magnesium_phosphate':
            # Magnesium phosphate cement hydration kinetics - extremely fast
            # MgO + KH2PO4 + H2O → MgKHPO4·6H2O (MCPM)
            
            # KH2PO4 hydration kinetics - very rapid dissolution
            temp_factor_kh2po4 = np.exp(-Ea['KH2PO4']/R * (1/T - 1/T_ref))
            if time_days < 0.01:
                # Initial stage - instantaneous dissolution
                alpha_kh2po4 = 1 - np.exp(-1000.0 * temp_factor_kh2po4 * nano_factor * chemical_factor * time_days)
            elif time_days < 0.05:
                # Accelerating stage
                alpha_kh2po4 = 0.9 + 0.1 * (1 - np.exp(-100.0 * temp_factor_kh2po4 * nano_factor * chemical_factor * (time_days - 0.01)))
            else:
                # Complete dissolution
                alpha_kh2po4 = 1.0
            degrees['KH2PO4'] = min(alpha_kh2po4 * water_factor, 1.0)  # Complete dissolution
            
            # MgO hydration kinetics - fast but controlled by reaction with phosphate
            temp_factor_mgo = np.exp(-Ea['MgO']/R * (1/T - 1/T_ref))
            if time_days < 0.01:
                # Initial stage - rapid reaction
                alpha_mgo = 1 - np.exp(-500.0 * temp_factor_mgo * nano_factor * chemical_factor * time_days)
            elif time_days < 0.1:
                # Accelerating stage
                alpha_mgo = 0.8 + 0.15 * (1 - np.exp(-50.0 * temp_factor_mgo * nano_factor * chemical_factor * (time_days - 0.01)))
            elif time_days < 0.5:
                # Decelerating stage
                alpha_mgo = 0.95 + 0.05 * (1 - np.exp(-10.0 * temp_factor_mgo * nano_factor * chemical_factor * (time_days - 0.1)))
            else:
                # Complete hydration
                alpha_mgo = 1.0
            degrees['MgO'] = min(alpha_mgo * water_factor, 1.0)  # Complete hydration
        elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
            # Composite cement systems - calculate hydration for all relevant minerals
            
            # C3S hydration kinetics
            if 'C3S' in self.clinker_composition and self.clinker_composition['C3S'] > 0:
                temp_factor_c3s = np.exp(-Ea['C3S']/R * (1/T - 1/T_ref))
                if time_days < 1:
                    alpha_c3s = 1 - np.exp(-5.0 * temp_factor_c3s * nano_factor * chemical_factor * time_days)
                elif time_days < 14:
                    alpha_c3s = 0.3 + 0.4 * (1 - np.exp(-0.8 * temp_factor_c3s * nano_factor * chemical_factor * (time_days - 1)))
                else:
                    alpha_c3s = 0.7 + 0.2 * (1 - np.exp(-0.1 * temp_factor_c3s * nano_factor * chemical_factor * (time_days - 14)))
                degrees['C3S'] = min(alpha_c3s * water_factor, 0.95)
            
            # C2S hydration kinetics
            if 'C2S' in self.clinker_composition and self.clinker_composition['C2S'] > 0:
                temp_factor_c2s = np.exp(-Ea['C2S']/R * (1/T - 1/T_ref))
                alpha_c2s = 1 - np.exp(-0.3 * temp_factor_c2s * nano_factor * chemical_factor * time_days**0.7)
                degrees['C2S'] = min(alpha_c2s * water_factor, 0.85)
            
            # C3A hydration kinetics
            if 'C3A' in self.clinker_composition and self.clinker_composition['C3A'] > 0:
                temp_factor_c3a = np.exp(-Ea['C3A']/R * (1/T - 1/T_ref))
                if time_days < 0.5:
                    alpha_c3a = 1 - np.exp(-15.0 * temp_factor_c3a * nano_factor * chemical_factor * c3a_factor * time_days)
                else:
                    alpha_c3a = 0.6 + 0.3 * (1 - np.exp(-0.3 * temp_factor_c3a * nano_factor * chemical_factor * c3a_factor * (time_days - 0.5)))
                degrees['C3A'] = min(alpha_c3a * water_factor, 0.98)
            
            # C4AF hydration kinetics
            if 'C4AF' in self.clinker_composition and self.clinker_composition['C4AF'] > 0:
                temp_factor_c4af = np.exp(-Ea['C4AF']/R * (1/T - 1/T_ref))
                if time_days < 1:
                    alpha_c4af = 1 - np.exp(-4.0 * temp_factor_c4af * nano_factor * chemical_factor * time_days)
                else:
                    alpha_c4af = 0.4 + 0.4 * (1 - np.exp(-0.4 * temp_factor_c4af * nano_factor * chemical_factor * (time_days - 1)))
                degrees['C4AF'] = min(alpha_c4af * water_factor, 0.90)
            
            # C4A3S hydration kinetics
            if 'C4A3S' in self.clinker_composition and self.clinker_composition['C4A3S'] > 0:
                temp_factor_c4a3s = np.exp(-Ea['C4A3S']/R * (1/T - 1/T_ref))
                if time_days < 0.2:
                    alpha_c4a3s = 1 - np.exp(-30.0 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * time_days)
                elif time_days < 1:
                    alpha_c4a3s = 0.7 + 0.2 * (1 - np.exp(-5.0 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * (time_days - 0.2)))
                else:
                    alpha_c4a3s = 0.9 + 0.1 * (1 - np.exp(-0.5 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * (time_days - 1)))
                degrees['C4A3S'] = min(alpha_c4a3s * water_factor, 0.99)
            
            # CaSO4 hydration kinetics
            if 'CaSO4' in self.clinker_composition and self.clinker_composition['CaSO4'] > 0:
                temp_factor_caso4 = np.exp(-Ea['CaSO4']/R * (1/T - 1/T_ref))
                alpha_caso4 = 1 - np.exp(-20.0 * temp_factor_caso4 * nano_factor * chemical_factor * time_days)
                degrees['CaSO4'] = min(alpha_caso4 * water_factor, 0.99)
        
        return degrees
    
    def calculate_hydration_products(self, cement_mass, hydration_degrees, fly_ash_mass=0, slag_mass=0, time_days=0, temperature=20, w_c=0.5):
        """Calculate hydration products based on CEMDATA07 reactions"""
        # Calculate mass of each mineral in cement
        mineral_mass = {}
        for mineral, fraction in self.clinker_composition.items():
            mineral_mass[mineral] = cement_mass * fraction
        
        # Calculate moles of each mineral
        mineral_moles = {}
        for mineral, mass in mineral_mass.items():
            mineral_moles[mineral] = mass * 1000 / self.molar_mass[mineral]  # Convert to grams, then calculate moles
        
        # Calculate hydration products based on CEMDATA07 reactions
        products = {
            'CSH': 0,              # Calcium silicate hydrate (jennite-type)
            'CASH': 0,             # Calcium aluminate silicate hydrate
            'CH': 0,               # Calcium hydroxide (Portlandite)
            'ettringite': 0,        # Ettringite
            'monosulphate': 0,      # Monosulphate
            'C3AH6': 0,            # C3AH6 (hydrogarnet)
            'C4AH13': 0,           # C4AH13
            'straetlingite': 0,      # Straetlingite
            'Fe-ettringite': 0,      # Fe-ettringite
            'hydrotalcite': 0,       # Hydrotalcite (HT)
            'AlOH': 0,             # Aluminum hydroxide
            'SiOH': 0,              # Silica gel
            'ettringite_sulpho': 0,  # Ettringite from sulphoaluminate hydration
            'thaumasite': 0,         # Thaumasite
            'CAH10': 0,             # Calcium aluminate hydrate (CAH10)
            'C2AH8': 0,             # Calcium aluminate hydrate (C2AH8)
            'AH3': 0,               # Aluminum hydroxide (Gibbsite)
            'MCPM': 0,              # Magnesium potassium phosphate hexahydrate
            'MgO': 0,               # Magnesium oxide (unreacted)
            'KH2PO4': 0             # Potassium dihydrogen phosphate (unreacted)
        }
        
        if self.cement_type == 'portland':
            # C3S hydration: C3S + 4.5H2O → C1.6667SH2.1 (jennite-type) + CH
            # Reaction: (CaO)3SiO2 + 4.5H2O → (CaO)1.6667(SiO2)(H2O)2.1 + Ca(OH)2
            if 'C3S' in mineral_moles and 'C3S' in hydration_degrees:
                c3s_moles = mineral_moles['C3S'] * hydration_degrees['C3S']
                products['CSH'] += c3s_moles
                products['CH'] += c3s_moles
            
            # C2S hydration: C2S + 3.3H2O → C0.8333SH1.3333 (tobermorite-type) + CH
            # Reaction: (CaO)2SiO2 + 3.3H2O → (CaO)0.8333(SiO2)(H2O)1.3333 + Ca(OH)2
            if 'C2S' in mineral_moles and 'C2S' in hydration_degrees:
                c2s_moles = mineral_moles['C2S'] * hydration_degrees['C2S']
                products['CSH'] += c2s_moles * 0.5  # Tobermorite-type has lower Ca/Si ratio
                products['CH'] += c2s_moles
            
            # C3A hydration: Different products based on sulfate availability
            if 'C3A' in mineral_moles and 'C3A' in hydration_degrees:
                c3a_moles = mineral_moles['C3A'] * hydration_degrees['C3A']
                # Assume sufficient sulfate for ettringite formation initially
                # C3A + 3CaSO4 + 32H2O → Ca6Al2(SO4)3(OH)12·26H2O (ettringite)
                products['ettringite'] += c3a_moles * 0.6  # 60% forms ettringite
                # Remaining C3A forms monosulphate
                # C3A + CaSO4 + 12H2O → Ca4Al2(SO4)(OH)12·6H2O (monosulphate)
                products['monosulphate'] += c3a_moles * 0.4  # 40% forms monosulphate
            
            # C4AF hydration: Forms Fe-ettringite and Fe-monosulphate
            if 'C4AF' in mineral_moles and 'C4AF' in hydration_degrees:
                c4af_moles = mineral_moles['C4AF'] * hydration_degrees['C4AF']
                # C4AF + 3CaSO4 + 32H2O → Ca6Fe2(SO4)3(OH)12·26H2O (Fe-ettringite)
                products['Fe-ettringite'] += c4af_moles
            
            # Straetlingite formation (from C3A and silica)
            # Ca2Al2SiO2(OH)10·3H2O
            if 'C3A' in mineral_moles and 'C3A' in hydration_degrees:
                c3a_moles = mineral_moles['C3A'] * hydration_degrees['C3A']
                products['straetlingite'] += c3a_moles * 0.1  # 10% of C3A forms straetlingite
        elif self.cement_type == 'sulphoaluminate':
            # C4A3S hydration: C4A3S + 2CaSO4 + 32H2O → 3Ca6Al2(SO4)3(OH)12·26H2O + 2Al(OH)3
            if 'C4A3S' in mineral_moles and 'C4A3S' in hydration_degrees:
                c4a3s_moles = mineral_moles['C4A3S'] * hydration_degrees['C4A3S']
                # Calculate available CaSO4
                caso4_moles = 0
                if 'CaSO4' in mineral_moles and 'CaSO4' in hydration_degrees:
                    caso4_moles = mineral_moles['CaSO4'] * hydration_degrees['CaSO4']
                
                # Determine limiting reactant
                required_caso4 = c4a3s_moles * 2
                actual_caso4 = min(caso4_moles, required_caso4)
                
                # Calculate ettringite formation
                ettringite_moles = (actual_caso4 / 2) * 3
                products['ettringite_sulpho'] += ettringite_moles
                
                # Calculate CH formation (from C4A3S hydration)
                # C4A3S + 18H2O → 4Ca(OH)2 + 3Al(OH)3 + CaSO4
                ch_moles = c4a3s_moles * 4
                products['CH'] += ch_moles
            
            # C2S hydration: C2S + 3.3H2O → C0.8333SH1.3333 (tobermorite-type) + CH
            if 'C2S' in mineral_moles and 'C2S' in hydration_degrees:
                c2s_moles = mineral_moles['C2S'] * hydration_degrees['C2S']
                products['CSH'] += c2s_moles * 0.5  # Tobermorite-type has lower Ca/Si ratio
                products['CH'] += c2s_moles
            
            # C4AF hydration: Forms Fe-ettringite and Fe-monosulphate
            if 'C4AF' in mineral_moles and 'C4AF' in hydration_degrees:
                c4af_moles = mineral_moles['C4AF'] * hydration_degrees['C4AF']
                # C4AF + 3CaSO4 + 32H2O → Ca6Fe2(SO4)3(OH)12·26H2O (Fe-ettringite)
                products['Fe-ettringite'] += c4af_moles
            
            # CaSO4 hydration (remaining after C4A3S reaction)
            if 'CaSO4' in mineral_moles and 'CaSO4' in hydration_degrees:
                total_caso4 = mineral_moles['CaSO4'] * hydration_degrees['CaSO4']
                used_caso4 = 0
                if 'C4A3S' in mineral_moles and 'C4A3S' in hydration_degrees:
                    c4a3s_moles = mineral_moles['C4A3S'] * hydration_degrees['C4A3S']
                    used_caso4 = min(total_caso4, c4a3s_moles * 2)
                remaining_caso4 = total_caso4 - used_caso4
                # Remaining CaSO4 may react with CH and silica to form thaumasite
                if remaining_caso4 > 0 and products['CH'] > 0:
                    # Thaumasite formation: Ca(OH)2 + CaSO4 + SiO2 + CO2 + 12H2O → Ca3Si(OH)6(CO3)(SO4)·12H2O
                    thaumasite_moles = min(remaining_caso4, products['CH'])
                    products['thaumasite'] += thaumasite_moles
                    products['CH'] -= thaumasite_moles
        elif self.cement_type == 'aluminate':
            # CA hydration: CA + 10H2O → CAH10 (at <25°C)
            # CA + 8H2O → C2AH8 + AH3 (at 25-35°C)
            # CA + 6H2O → C3AH6 + 2AH3 (at >35°C)
            # Assume room temperature (20°C) - CAH10 formation
            if 'CA' in mineral_moles and 'CA' in hydration_degrees:
                ca_moles = mineral_moles['CA'] * hydration_degrees['CA']
                products['CAH10'] += ca_moles
                products['AH3'] += ca_moles * 0  # At 20°C, no AH3 formation
            
            # CA2 hydration: CA2 + 11H2O → C2AH8 + 2AH3
            if 'CA2' in mineral_moles and 'CA2' in hydration_degrees:
                ca2_moles = mineral_moles['CA2'] * hydration_degrees['CA2']
                products['C2AH8'] += ca2_moles
                products['AH3'] += ca2_moles * 2
            
            # C12A7 hydration: C12A7 + 36H2O → 4C3AH6 + 6AH3
            if 'C12A7' in mineral_moles and 'C12A7' in hydration_degrees:
                c12a7_moles = mineral_moles['C12A7'] * hydration_degrees['C12A7']
                products['C3AH6'] += c12a7_moles * 4
                products['AH3'] += c12a7_moles * 6
            
            # C2S hydration: C2S + 3.3H2O → C0.8333SH1.3333 (tobermorite-type) + CH
            if 'C2S' in mineral_moles and 'C2S' in hydration_degrees:
                c2s_moles = mineral_moles['C2S'] * hydration_degrees['C2S']
                products['CSH'] += c2s_moles * 0.5  # Tobermorite-type has lower Ca/Si ratio
                products['CH'] += c2s_moles
        elif self.cement_type == 'magnesium_phosphate':
            # Magnesium phosphate cement hydration: MgO + KH2PO4 + 6H2O → MgKHPO4·6H2O (MCPM)
            if 'MgO' in mineral_moles and 'MgO' in hydration_degrees and 'KH2PO4' in mineral_moles and 'KH2PO4' in hydration_degrees:
                mgo_moles = mineral_moles['MgO'] * hydration_degrees['MgO']
                kh2po4_moles = mineral_moles['KH2PO4'] * hydration_degrees['KH2PO4']
                
                # Determine limiting reactant
                mcp_moles = min(mgo_moles, kh2po4_moles)
                
                # Calculate MCPM formation
                products['MCPM'] += mcp_moles
                
                # Excess reactants
                if mgo_moles > kh2po4_moles:
                    # Excess MgO
                    products['MgO'] += mgo_moles - kh2po4_moles
                else:
                    # Excess KH2PO4
                    products['KH2PO4'] += kh2po4_moles - mgo_moles
        elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
            # Composite cement systems - calculate hydration products for all relevant minerals
            
            # Portland cement minerals hydration
            if 'C3S' in mineral_moles and 'C3S' in hydration_degrees:
                c3s_moles = mineral_moles['C3S'] * hydration_degrees['C3S']
                products['CSH'] += c3s_moles
                products['CH'] += c3s_moles
            
            if 'C2S' in mineral_moles and 'C2S' in hydration_degrees:
                c2s_moles = mineral_moles['C2S'] * hydration_degrees['C2S']
                products['CSH'] += c2s_moles * 0.5
                products['CH'] += c2s_moles
            
            if 'C3A' in mineral_moles and 'C3A' in hydration_degrees:
                c3a_moles = mineral_moles['C3A'] * hydration_degrees['C3A']
                products['ettringite'] += c3a_moles * 0.6
                products['monosulphate'] += c3a_moles * 0.4
            
            if 'C4AF' in mineral_moles and 'C4AF' in hydration_degrees:
                c4af_moles = mineral_moles['C4AF'] * hydration_degrees['C4AF']
                products['Fe-ettringite'] += c4af_moles
            
            # Sulphoaluminate cement minerals hydration
            if 'C4A3S' in mineral_moles and 'C4A3S' in hydration_degrees:
                c4a3s_moles = mineral_moles['C4A3S'] * hydration_degrees['C4A3S']
                caso4_moles = 0
                if 'CaSO4' in mineral_moles and 'CaSO4' in hydration_degrees:
                    caso4_moles = mineral_moles['CaSO4'] * hydration_degrees['CaSO4']
                
                required_caso4 = c4a3s_moles * 2
                actual_caso4 = min(caso4_moles, required_caso4)
                
                ettringite_moles = (actual_caso4 / 2) * 3
                products['ettringite_sulpho'] += ettringite_moles
                
                ch_moles = c4a3s_moles * 4
                products['CH'] += ch_moles
            
            # CaSO4 hydration (remaining after C4A3S reaction)
            if 'CaSO4' in mineral_moles and 'CaSO4' in hydration_degrees:
                total_caso4 = mineral_moles['CaSO4'] * hydration_degrees['CaSO4']
                used_caso4 = 0
                if 'C4A3S' in mineral_moles and 'C4A3S' in hydration_degrees:
                    c4a3s_moles = mineral_moles['C4A3S'] * hydration_degrees['C4A3S']
                    used_caso4 = min(total_caso4, c4a3s_moles * 2)
                remaining_caso4 = total_caso4 - used_caso4
                if remaining_caso4 > 0 and products['CH'] > 0:
                    thaumasite_moles = min(remaining_caso4, products['CH'])
                    products['thaumasite'] += thaumasite_moles
                    products['CH'] -= thaumasite_moles
        
        # Slag hydration based on Chen & Brouwers' model (Model 3)
        if slag_mass > 0:
            # Slag reactivity depends on time, temperature, and w/c ratio
            # Based on Kolani's model and experimental data
            slag_reactivity = 0.34 * (1 - np.exp(-0.005 * time_days))
            # Temperature effect on slag reactivity
            T_ref = 293.15  # Reference temperature (20°C) in K
            T = 273.15 + temperature  # Current temperature in K
            temp_factor_slag = np.exp(-40000/8.314 * (1/T - 1/T_ref))
            slag_reactivity *= temp_factor_slag
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)  # Assume 0.45 is minimum w/c for full hydration
            slag_reactivity *= water_factor
            # Limit maximum reactivity to 34%
            slag_reactivity = min(slag_reactivity, 0.34)
            
            # Slag composition (typical blast furnace slag) from Kolani's paper
            slag_composition = {
                'CaO': 0.423,  # 42.3%
                'SiO2': 0.359,  # 35.9%
                'Al2O3': 0.112, # 11.2%
                'MgO': 0.08,   # 8.0%
                'Fe2O3': 0.003, # 0.3%
                'SO3': 0.002   # 0.2%
            }
            
            # Calculate slag moles
            slag_molar_mass = 0
            for oxide, fraction in slag_composition.items():
                if oxide == 'CaO':
                    slag_molar_mass += fraction * 56.08
                elif oxide == 'SiO2':
                    slag_molar_mass += fraction * 60.08
                elif oxide == 'Al2O3':
                    slag_molar_mass += fraction * 101.96
                elif oxide == 'MgO':
                    slag_molar_mass += fraction * 40.31
                elif oxide == 'Fe2O3':
                    slag_molar_mass += fraction * 159.69
                elif oxide == 'SO3':
                    slag_molar_mass += fraction * 80.07
            
            slag_moles = slag_mass * 1000 / slag_molar_mass
            reacted_slag_moles = slag_moles * slag_reactivity
            
            # Slag hydration consumes CH and forms C-A-S-H
            # According to Chen & Brouwers' model (Model 3), part of CH enters C-A-S-H
            # C/S ratio in C-A-S-H decreases with slag content
            slag_ratio = slag_mass / (cement_mass + slag_mass)
            c_s_ratio = 1.8 - 0.8 * slag_ratio  # Typical C/S ratio
            a_s_ratio = 0.1 + 0.2 * slag_ratio  # Typical A/S ratio
            
            # Calculate CH consumption by slag
            # Based on Chen & Brouwers' model, CH consumption depends on slag reactivity
            ch_consumption = reacted_slag_moles * (1 - c_s_ratio)  # More accurate CH consumption
            products['CH'] = max(0, products['CH'] - ch_consumption)
            
            # Form C-A-S-H from slag
            products['CASH'] += reacted_slag_moles
            
            # Form hydrotalcite (HT) from MgO in slag
            products['hydrotalcite'] += reacted_slag_moles * slag_composition['MgO']
        
        # Fly ash hydration (improved kinetics based on CEMDATA07)
        if fly_ash_mass > 0:
            # Fly ash reactivity depends on time, temperature, and w/c ratio
            # Assume 30% of fly ash reacts by 90 days at 20°C
            fly_ash_reactivity = 0.3 * (1 - np.exp(-0.02 * time_days))
            # Temperature effect on fly ash reactivity
            T_ref = 293.15  # Reference temperature (20°C) in K
            T = 273.15 + temperature  # Current temperature in K
            temp_factor_fa = np.exp(-35000/8.314 * (1/T - 1/T_ref))
            fly_ash_reactivity *= temp_factor_fa
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)  # Assume 0.45 is minimum w/c for full hydration
            fly_ash_reactivity *= water_factor
            # Limit maximum reactivity to 30%
            fly_ash_reactivity = min(fly_ash_reactivity, 0.3)
            
            fly_ash_moles = fly_ash_mass * 1000 / 60  # Approximate molar mass of fly ash
            products['CSH'] += fly_ash_moles * fly_ash_reactivity * 0.7
            products['SiOH'] += fly_ash_moles * fly_ash_reactivity * 0.3
        
        return products
    
    def calculate_heat_generation(self, cement_mass, hydration_degrees, fly_ash_mass=0, slag_mass=0, time_days=0, temperature=20, w_c=0.5):
        """Calculate heat generation based on CEMDATA07 thermodynamic data"""
        total_heat = 0
        
        # Calculate mass of each mineral in cement
        for mineral, fraction in self.clinker_composition.items():
            if mineral in hydration_degrees and mineral in self.hydration_heat:
                mineral_mass = cement_mass * fraction
                # Take absolute value since hydration is exothermic
                # Hydration heat is in J/g, so multiply by mass in g
                heat = abs(mineral_mass * 1000 * self.hydration_heat[mineral] * hydration_degrees[mineral])
                total_heat += heat
        
        # Fly ash hydration heat (simplified)
        if fly_ash_mass > 0:
            # Assume fly ash generates about 10% of cement heat
            fly_ash_heat = fly_ash_mass * 1000 * 25  # Approximate heat generation in J/g (10% of cement)
            total_heat += fly_ash_heat
        
        # Slag hydration heat based on Chen & Brouwers' model
        if slag_mass > 0:
            # Slag reactivity depends on time, temperature, and w/c ratio
            # Based on Kolani's model and experimental data
            slag_reactivity = 0.34 * (1 - np.exp(-0.005 * time_days))
            # Temperature effect on slag reactivity
            T_ref = 293.15  # Reference temperature (20°C) in K
            T = 273.15 + temperature  # Current temperature in K
            temp_factor_slag = np.exp(-40000/8.314 * (1/T - 1/T_ref))
            slag_reactivity *= temp_factor_slag
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)  # Assume 0.45 is minimum w/c for full hydration
            slag_reactivity *= water_factor
            # Limit maximum reactivity to 34%
            slag_reactivity = min(slag_reactivity, 0.34)
            
            # Slag generates about 40-60% of cement heat based on literature
            # According to Chen & Brouwers' model, slag hydration heat depends on reactivity
            slag_heat = slag_mass * 1000 * 150  # Approximate heat generation in J/g (40% of cement)
            total_heat += slag_heat * slag_reactivity
        
        return total_heat / 1000  # Convert to kJ
    
    def calculate_volume_change(self, cement_mass, hydration_degrees, water_mass, fly_ash_mass=0, slag_mass=0, time_days=0, temperature=20, w_c=0.5):
        """Calculate volume change based on CEMDATA18 molar volumes"""
        # Calculate mass of each mineral in cement
        mineral_mass = {}
        for mineral, fraction in self.clinker_composition.items():
            mineral_mass[mineral] = cement_mass * fraction
        
        # Calculate moles of each mineral
        mineral_moles = {}
        for mineral, mass in mineral_mass.items():
            mineral_moles[mineral] = mass * 1000 / self.molar_mass[mineral]
        
        # Calculate reacted moles
        reacted_moles = {}
        for mineral, moles in mineral_moles.items():
            if mineral in hydration_degrees:
                reacted_moles[mineral] = moles * hydration_degrees[mineral]
            else:
                reacted_moles[mineral] = 0
        
        # Calculate volume of unreacted cement minerals
        unreacted_volume = 0
        for mineral, moles in mineral_moles.items():
            if mineral in self.molar_volume:
                unreacted_volume += (moles - reacted_moles[mineral]) * self.molar_volume[mineral] / 1000000  # Convert to m³
        
        # Calculate hydration products
        products = self.calculate_hydration_products(cement_mass, hydration_degrees, fly_ash_mass, slag_mass, time_days, temperature, w_c)
        
        # Add molar volumes for new products
        self.molar_volume['AlOH'] = 31.96  # Aluminum hydroxide
        self.molar_volume['SiOH'] = 29.0   # Silica gel
        self.molar_volume['CASH'] = 85.0   # C-A-S-H (calcium aluminate silicate hydrate)
        self.molar_volume['hydrotalcite'] = 150.0  # Hydrotalcite (Mg6Al2CO3(OH)16·4H2O)
        self.molar_volume['ettringite_sulpho'] = 707  # Ettringite from sulphoaluminate hydration
        self.molar_volume['thaumasite'] = 650  # Thaumasite
        
        # Calculate volume of hydration products
        products_volume = 0
        for product, moles in products.items():
            if product in self.molar_volume:
                products_volume += moles * self.molar_volume[product] / 1000000  # Convert to m³
        
        # Calculate water consumption
        water_consumption = 0
        
        if self.cement_type == 'portland':
            # C3S hydration: C3S + 3H2O → CSH + Ca(OH)2
            if 'C3S' in reacted_moles:
                water_consumption += reacted_moles['C3S'] * 3  # 3 moles water per mole C3S
            # C2S hydration: C2S + 2H2O → CSH + Ca(OH)2
            if 'C2S' in reacted_moles:
                water_consumption += reacted_moles['C2S'] * 2  # 2 moles water per mole C2S
            # C3A hydration: C3A + 3CaSO4 + 32H2O → C6A(S)3H32 (AFt)
            if 'C3A' in reacted_moles:
                water_consumption += reacted_moles['C3A'] * 32  # 32 moles water per mole C3A
            # C4AF hydration: C4AF + 2CaSO4 + 20H2O → C6(AF)(S)2H20 (AFm-like)
            if 'C4AF' in reacted_moles:
                water_consumption += reacted_moles['C4AF'] * 20  # 20 moles water per mole C4AF
        elif self.cement_type == 'sulphoaluminate':
            # C4A3S hydration: C4A3S + 2CaSO4 + 32H2O → 3Ca6Al2(SO4)3(OH)12·26H2O + 2Al(OH)3
            if 'C4A3S' in reacted_moles:
                water_consumption += reacted_moles['C4A3S'] * 32  # 32 moles water per mole C4A3S
            # C2S hydration: C2S + 3.3H2O → C0.8333SH1.3333 (tobermorite-type) + CH
            if 'C2S' in reacted_moles:
                water_consumption += reacted_moles['C2S'] * 3.3  # 3.3 moles water per mole C2S
            # C4AF hydration: C4AF + 3CaSO4 + 32H2O → Ca6Fe2(SO4)3(OH)12·26H2O (Fe-ettringite)
            if 'C4AF' in reacted_moles:
                water_consumption += reacted_moles['C4AF'] * 32  # 32 moles water per mole C4AF
            # CaSO4 hydration: CaSO4 + 2H2O → CaSO4·2H2O (gypsum)
            if 'CaSO4' in reacted_moles:
                water_consumption += reacted_moles['CaSO4'] * 2  # 2 moles water per mole CaSO4
        elif self.cement_type == 'aluminate':
            # CA hydration: CA + 10H2O → CAH10 (at <25°C)
            if 'CA' in reacted_moles:
                water_consumption += reacted_moles['CA'] * 10  # 10 moles water per mole CA
            # CA2 hydration: CA2 + 11H2O → C2AH8 + 2AH3
            if 'CA2' in reacted_moles:
                water_consumption += reacted_moles['CA2'] * 11  # 11 moles water per mole CA2
            # C12A7 hydration: C12A7 + 36H2O → 4C3AH6 + 6AH3
            if 'C12A7' in reacted_moles:
                water_consumption += reacted_moles['C12A7'] * 36  # 36 moles water per mole C12A7
            # C2S hydration: C2S + 3.3H2O → C0.8333SH1.3333 (tobermorite-type) + CH
            if 'C2S' in reacted_moles:
                water_consumption += reacted_moles['C2S'] * 3.3  # 3.3 moles water per mole C2S
        elif self.cement_type == 'magnesium_phosphate':
            # Magnesium phosphate cement hydration: MgO + KH2PO4 + 6H2O → MgKHPO4·6H2O (MCPM)
            if 'MgO' in reacted_moles and 'KH2PO4' in reacted_moles:
                mgo_moles = reacted_moles['MgO']
                kh2po4_moles = reacted_moles['KH2PO4']
                # Determine limiting reactant
                mcp_moles = min(mgo_moles, kh2po4_moles)
                # Water consumption: 6 moles water per mole MCPM
                water_consumption += mcp_moles * 6
        elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
            # Composite cement systems - calculate water consumption for all relevant minerals
            
            # Portland cement minerals water consumption
            if 'C3S' in reacted_moles:
                water_consumption += reacted_moles['C3S'] * 3
            if 'C2S' in reacted_moles:
                water_consumption += reacted_moles['C2S'] * 2
            if 'C3A' in reacted_moles:
                water_consumption += reacted_moles['C3A'] * 32
            if 'C4AF' in reacted_moles:
                water_consumption += reacted_moles['C4AF'] * 20
            
            # Sulphoaluminate cement minerals water consumption
            if 'C4A3S' in reacted_moles:
                water_consumption += reacted_moles['C4A3S'] * 32
            if 'CaSO4' in reacted_moles:
                water_consumption += reacted_moles['CaSO4'] * 2
        
        # Fly ash hydration water consumption
        if fly_ash_mass > 0:
            # Fly ash reactivity depends on time, temperature, and w/c ratio
            fly_ash_reactivity = 0.3 * (1 - np.exp(-0.02 * time_days))
            # Temperature effect on fly ash reactivity
            T_ref = 293.15  # Reference temperature (20°C) in K
            T = 273.15 + temperature  # Current temperature in K
            temp_factor_fa = np.exp(-35000/8.314 * (1/T - 1/T_ref))
            fly_ash_reactivity *= temp_factor_fa
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)  # Assume 0.45 is minimum w/c for full hydration
            fly_ash_reactivity *= water_factor
            # Limit maximum reactivity to 30%
            fly_ash_reactivity = min(fly_ash_reactivity, 0.3)
            
            fly_ash_moles = fly_ash_mass * 1000 / 60
            water_consumption += fly_ash_moles * fly_ash_reactivity * 2  # Approximate water consumption
        # Slag hydration water consumption
        if slag_mass > 0:
            # Slag reactivity depends on time, temperature, and w/c ratio
            slag_reactivity = 0.34 * (1 - np.exp(-0.005 * time_days))
            # Temperature effect on slag reactivity
            T_ref = 293.15  # Reference temperature (20°C) in K
            T = 273.15 + temperature  # Current temperature in K
            temp_factor_slag = np.exp(-40000/8.314 * (1/T - 1/T_ref))
            slag_reactivity *= temp_factor_slag
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)  # Assume 0.45 is minimum w/c for full hydration
            slag_reactivity *= water_factor
            # Limit maximum reactivity to 34%
            slag_reactivity = min(slag_reactivity, 0.34)
            
            # Slag hydration consumes water
            slag_molar_mass = 0
            slag_composition = {
                'CaO': 0.423, 'SiO2': 0.359, 'Al2O3': 0.112, 'MgO': 0.08, 'Fe2O3': 0.003, 'SO3': 0.002
            }
            for oxide, fraction in slag_composition.items():
                if oxide == 'CaO':
                    slag_molar_mass += fraction * 56.08
                elif oxide == 'SiO2':
                    slag_molar_mass += fraction * 60.08
                elif oxide == 'Al2O3':
                    slag_molar_mass += fraction * 101.96
                elif oxide == 'MgO':
                    slag_molar_mass += fraction * 40.31
                elif oxide == 'Fe2O3':
                    slag_molar_mass += fraction * 159.69
                elif oxide == 'SO3':
                    slag_molar_mass += fraction * 80.07
            
            slag_moles = slag_mass * 1000 / slag_molar_mass
            water_consumption += slag_moles * slag_reactivity * 2  # Approximate water consumption
        
        # Calculate initial water volume
        initial_water_volume = water_mass / self.densities['Water']
        
        # Calculate remaining water volume
        remaining_water_moles = (water_mass * 1000 / self.molar_mass['H2O']) - water_consumption
        remaining_water_volume = max(0, remaining_water_moles * self.molar_volume['H2O'] / 1000000)  # Convert to m³
        
        # Calculate initial cement volume
        initial_cement_volume = cement_mass / self.densities['Cement']
        
        # Calculate initial fly ash volume
        initial_fly_ash_volume = fly_ash_mass / self.densities['Fly Ash'] if fly_ash_mass > 0 else 0
        
        # Calculate initial slag volume
        initial_slag_volume = slag_mass / 2900 if slag_mass > 0 else 0  # Slag density ~2900 kg/m³
        
        # Calculate total initial volume
        initial_total_volume = initial_cement_volume + initial_water_volume + initial_fly_ash_volume + initial_slag_volume
        
        # Calculate total final volume
        final_total_volume = unreacted_volume + products_volume + remaining_water_volume
        
        # Calculate volume change
        volume_change = final_total_volume - initial_total_volume
        
        return volume_change
    
    def calculate_strength(self, time_days, w_c=0.5, cement_strength_class='C32.5', nano_materials=None):
        """Calculate concrete strength development with age
        
        Args:
            time_days: Age of concrete in days
            w_c: Water-cement ratio
            cement_strength_class: Cement strength class (C32.5, C42.5, C52.5)
            nano_materials: Dictionary of nano materials and their mass fractions (default: None)
        
        Returns:
            Dictionary of strength values (MPa) for different types:
            - 'compressive': Compressive strength
            - 'flexural': Flexural strength
            - 'tensile': Tensile strength
        """
        # Base strength at 28 days based on cement class
        base_strength = {
            'C32.5': 32.5,
            'C42.5': 42.5,
            'C52.5': 52.5
        }.get(cement_strength_class, 32.5)
        
        # Water-cement ratio factor (Abrams' law)
        w_c_factor = 1 / (0.4 + 0.6 * w_c)
        
        # Age factor - different models for different cement types
        if self.cement_type == 'portland':
            # Portland cement strength development model
            if time_days < 1:
                age_factor = 0.3 * (time_days / 28) ** 0.3
            elif time_days < 3:
                age_factor = 0.5 * (time_days / 28) ** 0.4
            elif time_days < 7:
                age_factor = 0.7 * (time_days / 28) ** 0.5
            elif time_days < 28:
                age_factor = (time_days / 28) ** 0.6
            else:
                age_factor = 1.0 + 0.2 * (1 - np.exp(-0.05 * (time_days - 28)))
        elif self.cement_type == 'sulphoaluminate':
            # Sulphoaluminate cement strength development model
            # Faster early strength development
            if time_days <= 0:
                # Zero strength at time 0
                age_factor = 0
            elif time_days < 0.5:
                # Very early age - rapid strength gain
                age_factor = 0 + 0.5 * (time_days / 0.5)
            elif time_days < 1:
                # 1 day strength - typically 40-60% of 28-day strength
                age_factor = 0.5 + 0.1 * ((time_days - 0.5) / 0.5)
            elif time_days < 3:
                # 3 day strength - typically 70-80% of 28-day strength
                age_factor = 0.6 + 0.15 * ((time_days - 1) / 2)
            elif time_days < 7:
                # 7 day strength - typically 90%+ of 28-day strength
                age_factor = 0.75 + 0.15 * ((time_days - 3) / 4)
            elif time_days < 28:
                # Approach 28-day strength
                age_factor = 0.9 + 0.1 * ((time_days - 7) / 21)
            else:
                # Beyond 28 days - minimal strength gain
                age_factor = 1.0 + 0.1 * (1 - np.exp(-0.1 * (time_days - 28)))
        elif self.cement_type == 'aluminate':
            # Aluminate cement strength development model
            # Very fast early strength development
            if time_days <= 0:
                # Zero strength at time 0
                age_factor = 0
            elif time_days < 0.1:
                # Very early age - extremely rapid strength gain
                age_factor = 0 + 0.4 * (time_days / 0.1)
            elif time_days < 0.5:
                # 12 hours strength - typically 30-40% of 28-day strength
                age_factor = 0.4 + 0.2 * ((time_days - 0.1) / 0.4)
            elif time_days < 1:
                # 1 day strength - typically 60-70% of 28-day strength
                age_factor = 0.6 + 0.15 * ((time_days - 0.5) / 0.5)
            elif time_days < 3:
                # 3 day strength - typically 80-90% of 28-day strength
                age_factor = 0.75 + 0.15 * ((time_days - 1) / 2)
            elif time_days < 7:
                # 7 day strength - typically 95%+ of 28-day strength
                age_factor = 0.9 + 0.05 * ((time_days - 3) / 4)
            elif time_days < 28:
                # Approach 28-day strength
                age_factor = 0.95 + 0.05 * ((time_days - 7) / 21)
            else:
                # Beyond 28 days - minimal strength gain, may even decrease at high temperatures
                age_factor = 1.0 + 0.05 * (1 - np.exp(-0.05 * (time_days - 28)))
        elif self.cement_type == 'magnesium_phosphate':
            # Magnesium phosphate cement strength development model
            # Extremely fast early strength development
            if time_days <= 0:
                # Zero strength at time 0
                age_factor = 0
            elif time_days < 0.01:
                # Very early age - instantaneous strength gain (minutes)
                age_factor = 0 + 0.5 * (time_days / 0.01)
            elif time_days < 0.05:
                # 1 hour strength - typically 30-40% of 28-day strength
                age_factor = 0.5 + 0.3 * ((time_days - 0.01) / 0.04)
            elif time_days < 0.1:
                # 2-3 hours strength - typically 60-70% of 28-day strength
                age_factor = 0.8 + 0.1 * ((time_days - 0.05) / 0.05)
            elif time_days < 0.5:
                # 12 hours strength - typically 80-90% of 28-day strength
                age_factor = 0.9 + 0.05 * ((time_days - 0.1) / 0.4)
            elif time_days < 1:
                # 1 day strength - typically 95%+ of 28-day strength
                age_factor = 0.95 + 0.05 * ((time_days - 0.5) / 0.5)
            elif time_days < 28:
                # Approach 28-day strength
                age_factor = 1.0
            else:
                # Beyond 28 days - minimal strength gain
                age_factor = 1.0 + 0.05 * (1 - np.exp(-0.05 * (time_days - 28)))
        elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
            # Composite cement systems strength development model
            # Combines fast early strength from sulphoaluminate cement and long-term strength from portland cement
            if time_days <= 0:
                # Zero strength at time 0
                age_factor = 0
            elif time_days < 0.5:
                # Very early age - rapid strength gain from sulphoaluminate cement
                age_factor = 0 + 0.4 * (time_days / 0.5)
            elif time_days < 1:
                # 1 day strength - typically 40-50% of 28-day strength
                age_factor = 0.4 + 0.2 * ((time_days - 0.5) / 0.5)
            elif time_days < 3:
                # 3 day strength - typically 60-70% of 28-day strength
                age_factor = 0.6 + 0.15 * ((time_days - 1) / 2)
            elif time_days < 7:
                # 7 day strength - typically 80-85% of 28-day strength
                age_factor = 0.75 + 0.1 * ((time_days - 3) / 4)
            elif time_days < 14:
                # 14 day strength - typically 90-95% of 28-day strength
                age_factor = 0.85 + 0.05 * ((time_days - 7) / 7)
            elif time_days < 28:
                # 28 day strength - full strength
                age_factor = 0.9 + 0.1 * ((time_days - 14) / 14)
            else:
                # Beyond 28 days - continued strength gain from portland cement
                age_factor = 1.0 + 0.15 * (1 - np.exp(-0.05 * (time_days - 28)))
        
        # Calculate nano materials strength enhancement factor
        nano_strength_factor = 1.0
        if nano_materials:
            for nano, mass in nano_materials.items():
                if nano in self.nano_effects and mass > 0:
                    # Calculate effect based on mass fraction
                    enhancement = self.nano_effects[nano].get('strength_enhancement', 1.0)
                    nano_strength_factor *= enhancement ** (mass / 5)  # Normalize by 5kg/m³
        
        # Limit nano strength factor to avoid unrealistic enhancement
        nano_strength_factor = min(nano_strength_factor, 2.0)
        
        # Calculate compressive strength
        compressive_strength = base_strength * w_c_factor * age_factor * nano_strength_factor
        
        # Calculate other strengths based on compressive strength
        # Typical relationships for concrete
        flexural_strength = 0.7 * compressive_strength ** 0.5
        tensile_strength = 0.3 * compressive_strength ** 0.5
        
        return {
            'compressive': compressive_strength,
            'flexural': flexural_strength,
            'tensile': tensile_strength
        }
    
    def calculate_adiabatic_temperature(self, mix_design, time_days_list, initial_temperature=20, mode='adiabatic', environment_temp=20, concrete_thickness=0.3, heat_transfer_coefficient=5):
        """Calculate temperature of concrete
        
        Args:
            mix_design: Concrete mix design dictionary
            time_days_list: List of time points in days
            initial_temperature: Initial temperature in °C (default: 20°C, room temperature)
            mode: Calculation mode ('adiabatic' or 'semi-adiabatic', default: 'adiabatic')
            environment_temp: Environment temperature in °C (default: 20°C)
            concrete_thickness: Concrete thickness in meters (default: 0.3m)
            heat_transfer_coefficient: Heat transfer coefficient in W/(m²·°C) (default: 5)
        
        Returns:
            Tuple of (temperature_rises, absolute_temperatures):
            - temperature_rises: List of temperature rises at each time point
            - absolute_temperatures: List of absolute temperatures at each time point
        """
        # Calculate mass of materials involved in hydration
        # Only consider cement, water, and fly ash as they contribute to heat generation
        reactive_mass = 0
        reactive_mass += mix_design.get('Cement', 0)
        reactive_mass += mix_design.get('Water', 0)
        reactive_mass += mix_design.get('Fly Ash', 0)
        
        # Calculate mass of all materials (to absorb heat)
        total_mass = 0
        for material, mass in mix_design.items():
            total_mass += mass
        
        # Calculate average specific heat capacity
        weighted_cp = 0
        total_weight = 0
        for material, mass in mix_design.items():
            if material in self.specific_heat:
                weighted_cp += mass * self.specific_heat[material]
                total_weight += mass
        
        if total_weight > 0:
            avg_cp = weighted_cp / total_weight
        else:
            avg_cp = self.specific_heat['Concrete']
        
        # Calculate concrete volume (assuming 1m³)
        concrete_volume = 1.0  # m³
        
        # Calculate concrete surface area (assuming slab geometry)
        # For a 1m³ slab with thickness t, surface area = 2*(1*1) + 4*(1*t) = 2 + 4t
        surface_area = 2 + 4 * concrete_thickness  # m²
        
        # Simulate hydration to get heat generation
        results = self.simulate_hydration(mix_design, time_days_list, initial_temperature)
        
        # Calculate temperature rise and absolute temperature at each time point
        temperature_rises = []
        absolute_temperatures = []
        
        if mode == 'adiabatic':
            # Adiabatic calculation - no heat loss
            for heat in results['heat_generation']:
                # Convert heat from kJ to J
                heat_joules = heat * 1000
                # Calculate temperature rise (ΔT = Q / (m * c))
                # Use total mass to account for all materials absorbing heat
                if total_mass > 0 and avg_cp > 0:
                    temp_rise = heat_joules / (total_mass * avg_cp)
                    # Limit temperature rise to realistic values
                    temp_rise = min(temp_rise, 80)  # Maximum realistic temperature rise
                else:
                    temp_rise = 0
                
                temperature_rises.append(temp_rise)
                absolute_temperatures.append(initial_temperature + temp_rise)
        else:  # semi-adiabatic
            # Semi-adiabatic calculation - simplified method
            # Calculate adiabatic temperature rise first
            adiabatic_rises = []
            for heat in results['heat_generation']:
                heat_joules = heat * 1000
                if total_mass > 0 and avg_cp > 0:
                    temp_rise = heat_joules / (total_mass * avg_cp)
                    temp_rise = min(temp_rise, 80)  # Maximum realistic temperature rise
                else:
                    temp_rise = 0
                adiabatic_rises.append(temp_rise)
            
            # Calculate semi-adiabatic temperature rise
            # Use a heat loss factor that increases with time
            for i, time_days in enumerate(time_days_list):
                # Calculate heat loss factor (0.7 to 0.9 based on time)
                if time_days < 1:
                    heat_loss_factor = 0.9  # Less heat loss in early stages
                elif time_days < 7:
                    heat_loss_factor = 0.85
                elif time_days < 28:
                    heat_loss_factor = 0.8
                else:
                    heat_loss_factor = 0.75  # More heat loss in later stages
                
                # Calculate semi-adiabatic temperature rise
                temp_rise = adiabatic_rises[i] * heat_loss_factor
                
                # Calculate absolute temperature
                current_temp = initial_temperature + temp_rise
                
                temperature_rises.append(temp_rise)
                absolute_temperatures.append(current_temp)
        
        return temperature_rises, absolute_temperatures
    
    def simulate_hydration(self, mix_design, time_days_list, temperature=20):
        """Simulate cement hydration process"""
        cement_mass = mix_design.get('Cement', 0)
        water_mass = mix_design.get('Water', 0)
        fly_ash_mass = mix_design.get('Fly Ash', 0)
        slag_mass = mix_design.get('Slag', 0)
        w_c = self.calculate_water_cement_ratio(mix_design)
        
        # Extract nano materials from mix design
        nano_materials = {}
        nano_keys = ['Nano SiO2', 'Nano Al2O3', 'Nano CaCO3', 'Nano CaO', 'Nano MgO', 'Graphene']
        for key in nano_keys:
            if key in mix_design and mix_design[key] > 0:
                nano_materials[key] = mix_design[key]
        
        # Extract chemical admixtures from mix design
        chemical_admixtures = {}
        chemical_keys = ['CaCl2', 'AlCl3', 'Na2SO4', 'NaOH', 'KOH', 'Na2CO3', 'K2CO3', 'Retarder', 'Superplasticizer', 'AirEntrainer', 'ViscosityModifier']
        for key in chemical_keys:
            if key in mix_design and mix_design[key] > 0:
                chemical_admixtures[key] = mix_design[key]
        
        results = {
            'time_days': time_days_list,
            'hydration_degrees': [],
            'heat_generation': [],
            'volume_change': [],
            'hydration_products': []
        }
        
        for time_days in time_days_list:
            # Calculate hydration degree with nano materials and chemical admixtures effect
            hydration_degrees = self.calculate_hydration_degree(time_days, temperature, w_c, nano_materials, chemical_admixtures)
            results['hydration_degrees'].append(hydration_degrees)
            
            # Calculate heat generation
            heat = self.calculate_heat_generation(cement_mass, hydration_degrees, fly_ash_mass, slag_mass, time_days, temperature, w_c)
            results['heat_generation'].append(heat)
            
            # Calculate volume change
            volume_change = self.calculate_volume_change(cement_mass, hydration_degrees, water_mass, fly_ash_mass, slag_mass, time_days, temperature, w_c)
            results['volume_change'].append(volume_change)
            
            # Calculate hydration products
            products = self.calculate_hydration_products(cement_mass, hydration_degrees, fly_ash_mass, slag_mass, time_days, temperature, w_c)
            results['hydration_products'].append(products)
        
        return results
    
    def plot_results(self, results, adiabatic_rises=None, semi_adiabatic_rises=None, strengths=None):
        """Plot results"""
        import matplotlib
        # Set non-interactive backend for headless environments
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        time_days = results['time_days']
        
        # Plot hydration degree
        if adiabatic_rises:
            plt.figure(figsize=(18, 10))
            
            plt.subplot(2, 3, 1)
            if self.cement_type == 'portland':
                minerals = ['C3S', 'C2S', 'C3A', 'C4AF']
            elif self.cement_type == 'sulphoaluminate':
                minerals = ['C4A3S', 'C2S', 'C4AF', 'CaSO4']
            elif self.cement_type == 'aluminate':
                minerals = ['CA', 'CA2', 'C12A7', 'C2S']
            elif self.cement_type == 'magnesium_phosphate':
                minerals = ['MgO', 'KH2PO4']
            elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
                # Composite cement systems - include all relevant minerals
                minerals = ['C3S', 'C2S', 'C3A', 'C4AF', 'C4A3S', 'CaSO4']
            for mineral in minerals:
                degrees = [d.get(mineral, 0) for d in results['hydration_degrees']]
                plt.plot(time_days, degrees, label=mineral)
            plt.xlabel('Time (days)')
            plt.ylabel('Hydration Degree')
            plt.title('Hydration Degree of Minerals vs Time')
            plt.legend()
            plt.grid(True)
            
            # Plot heat generation
            plt.subplot(2, 3, 2)
            plt.plot(time_days, results['heat_generation'])
            plt.xlabel('Time (days)')
            plt.ylabel('Heat Generation (kJ)')
            plt.title('Cement Hydration Heat')
            plt.grid(True)
            
            # Plot volume change
            plt.subplot(2, 3, 3)
            plt.plot(time_days, results['volume_change'])
            plt.xlabel('Time (days)')
            plt.ylabel('Volume Change (m³)')
            plt.title('Cement Hydration Volume Change')
            plt.grid(True)
            
            # Plot hydration products
            plt.subplot(2, 3, 4)
            if self.cement_type == 'portland':
                products = ['CSH', 'CH', 'ettringite', 'monosulphate', 'CASH', 'hydrotalcite']
            elif self.cement_type == 'sulphoaluminate':
                products = ['CSH', 'CH', 'ettringite_sulpho', 'Fe-ettringite', 'thaumasite']
            elif self.cement_type == 'aluminate':
                products = ['CAH10', 'C2AH8', 'C3AH6', 'AH3', 'CSH', 'CH']
            elif self.cement_type == 'magnesium_phosphate':
                products = ['MCPM', 'MgO', 'KH2PO4']
            elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
                # Composite cement systems - include all relevant products
                products = ['CSH', 'CH', 'ettringite', 'ettringite_sulpho', 'Fe-ettringite', 'thaumasite', 'CASH', 'hydrotalcite']
            for product in products:
                amounts = [p.get(product, 0) for p in results['hydration_products']]
                plt.plot(time_days, amounts, label=product)
            plt.xlabel('Time (days)')
            plt.ylabel('Product Moles (mol)')
            plt.title('Hydration Products Formation')
            plt.legend()
            plt.grid(True)
            
            # Plot temperature rise comparison
            plt.subplot(2, 3, 5)
            plt.plot(time_days, adiabatic_rises, label='Adiabatic', linewidth=2)
            if semi_adiabatic_rises:
                plt.plot(time_days, semi_adiabatic_rises, label='Semi-Adiabatic', linewidth=2, linestyle='--')
            plt.xlabel('Time (days)')
            plt.ylabel('Temperature Rise (°C)')
            plt.title('Temperature Rise Comparison')
            plt.legend()
            plt.grid(True)
            
            # Plot strength development
            if strengths:
                plt.subplot(2, 3, 6)
                compressive = [s['compressive'] for s in strengths]
                flexural = [s['flexural'] for s in strengths]
                tensile = [s['tensile'] for s in strengths]
                plt.plot(time_days, compressive, label='Compressive', linewidth=2)
                plt.plot(time_days, flexural, label='Flexural', linewidth=2, linestyle='--')
                plt.plot(time_days, tensile, label='Tensile', linewidth=2, linestyle=':')
                plt.xlabel('Time (days)')
                plt.ylabel('Strength (MPa)')
                plt.title('Strength Development with Age')
                plt.legend()
                plt.grid(True)
        else:
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            if self.cement_type == 'portland':
                minerals = ['C3S', 'C2S', 'C3A', 'C4AF']
            elif self.cement_type == 'sulphoaluminate':
                minerals = ['C4A3S', 'C2S', 'C4AF', 'CaSO4']
            elif self.cement_type == 'aluminate':
                minerals = ['CA', 'CA2', 'C12A7', 'C2S']
            elif self.cement_type == 'magnesium_phosphate':
                minerals = ['MgO', 'KH2PO4']
            for mineral in minerals:
                degrees = [d.get(mineral, 0) for d in results['hydration_degrees']]
                plt.plot(time_days, degrees, label=mineral)
            plt.xlabel('Time (days)')
            plt.ylabel('Hydration Degree')
            plt.title('Hydration Degree of Minerals vs Time')
            plt.legend()
            plt.grid(True)
            
            # Plot heat generation
            plt.subplot(2, 2, 2)
            plt.plot(time_days, results['heat_generation'])
            plt.xlabel('Time (days)')
            plt.ylabel('Heat Generation (kJ)')
            plt.title('Cement Hydration Heat')
            plt.grid(True)
            
            # Plot volume change
            plt.subplot(2, 2, 3)
            plt.plot(time_days, results['volume_change'])
            plt.xlabel('Time (days)')
            plt.ylabel('Volume Change (m³)')
            plt.title('Cement Hydration Volume Change')
            plt.grid(True)
            
            # Plot hydration products
            plt.subplot(2, 2, 4)
            if self.cement_type == 'portland':
                products = ['CSH', 'CH', 'ettringite', 'monosulphate', 'CASH', 'hydrotalcite']
            elif self.cement_type == 'sulphoaluminate':
                products = ['CSH', 'CH', 'ettringite_sulpho', 'Fe-ettringite', 'thaumasite']
            elif self.cement_type == 'aluminate':
                products = ['CAH10', 'C2AH8', 'C3AH6', 'AH3', 'CSH', 'CH']
            elif self.cement_type == 'magnesium_phosphate':
                products = ['MCPM', 'MgO', 'KH2PO4']
            elif self.cement_type in ['portland_sulphoaluminate', 'portland_sulphoaluminate_gypsum']:
                # Composite cement systems - include all relevant products
                products = ['CSH', 'CH', 'ettringite', 'ettringite_sulpho', 'Fe-ettringite', 'thaumasite', 'CASH', 'hydrotalcite']
            for product in products:
                amounts = [p.get(product, 0) for p in results['hydration_products']]
                plt.plot(time_days, amounts, label=product)
            plt.xlabel('Time (days)')
            plt.ylabel('Product Moles (mol)')
            plt.title('Hydration Products Formation')
            plt.legend()
            plt.grid(True)
        
        plt.tight_layout()
        plt.savefig('cement_hydration_results.png', dpi=150, bbox_inches='tight')
        plt.close()  # Close the figure to free memory
    
    def calculate_chloride_diffusion(self, depth_mm, concentration, time_days):
        """Calculate chloride diffusion coefficient
        
        Args:
            depth_mm: List of depths in mm
            concentration: List of chloride concentrations
            time_days: Exposure time in days
        
        Returns:
            Dictionary with diffusion coefficient and fitting parameters
        """
        results = ChlorideDiffusion.calculate_diffusion_coefficient(depth_mm, concentration, time_days)
        if results:
            ChlorideDiffusion.plot_concentration_profile(depth_mm, concentration, results, 'concentration_profile.png')
        return results
    
    def predict_strength_ml(self, inputs=None):
        """Predict concrete strength using machine learning
        
        Args:
            inputs: Dictionary of input features
        
        Returns:
            Dictionary of predicted strengths from different models
        """
        predictor = MLStrengthPrediction()
        if inputs is None:
            inputs = predictor.get_default_inputs()
        results = predictor.predict_strength(inputs)
        return results

def main():
    # Example mix design (kg/m³) with slag, nano materials, and chemical admixtures
    mix_design = {
        'Water': 180,
        'Cement': 210,  # Reduced cement for slag substitution
        'Slag': 90,      # Added slag (30% substitution)
        'Fly Ash': 50,
        'Nano SiO2': 5,   # Added nano SiO2
        'Nano Al2O3': 3,  # Added nano Al2O3
        # Chemical admixtures
        'CaCl2': 2,      # Accelerator (2 kg/m³)
        'Na2SO4': 3,     # Accelerator (3 kg/m³)
        'Superplasticizer': 4,  # Water reducer (4 kg/m³)
        'Sand': 700,
        'Aggregate': 1000,
        'Steel Fiber': 50
    }
    
    # Simulation time points (days)
    time_days_list = [0, 1, 3, 7, 14, 28, 56, 90]
    
    # Create hydration simulator
    simulator = CementHydration()
    
    # Calculate water-cement ratio
    w_c = simulator.calculate_water_cement_ratio(mix_design)
    
    # Extract nano materials from mix design
    nano_materials = {}
    nano_keys = ['Nano SiO2', 'Nano Al2O3', 'Nano CaCO3', 'Nano CaO', 'Nano MgO', 'Graphene']
    for key in nano_keys:
        if key in mix_design and mix_design[key] > 0:
            nano_materials[key] = mix_design[key]
    
    # Simulate hydration process at 20°C (standard temperature)
    initial_temperature = 20  # Room temperature
    results = simulator.simulate_hydration(mix_design, time_days_list, initial_temperature)
    
    # Calculate adiabatic temperature
    adiabatic_rises, adiabatic_temps = simulator.calculate_adiabatic_temperature(mix_design, time_days_list, initial_temperature, mode='adiabatic')
    
    # Calculate semi-adiabatic temperature
    semi_adiabatic_rises, semi_adiabatic_temps = simulator.calculate_adiabatic_temperature(mix_design, time_days_list, initial_temperature, mode='semi-adiabatic')
    
    # Calculate strength development with nano materials effect
    strengths = []
    for time_days in time_days_list:
        strength = simulator.calculate_strength(time_days, w_c, 'C42.5', nano_materials)
        strengths.append(strength)
    
    # Generate and save plots
    simulator.plot_results(results, adiabatic_rises, semi_adiabatic_rises, strengths)
    
    # Write results to file
    with open('hydration_results.txt', 'w', encoding='utf-8') as f:
        f.write(f"Water-cement ratio: {w_c:.2f}\n")
        f.write(f"Initial temperature: {initial_temperature:.1f}°C\n")
        f.write("\nCement Hydration Simulation Results:\n")
        f.write("Time(days) | Heat(kJ) | Volume Change(m³) | Adiabatic Rise(°C) | Semi-Adiabatic Rise(°C)\n")
        f.write("-" * 95 + "\n")
        for i, time in enumerate(time_days_list):
            heat = results['heat_generation'][i]
            volume = results['volume_change'][i]
            adiabatic_rise = adiabatic_rises[i]
            semi_adiabatic_rise = semi_adiabatic_rises[i]
            f.write(f"{time:6.1f} | {heat:10.2f} | {volume:12.6f} | {adiabatic_rise:15.2f} | {semi_adiabatic_rise:19.2f}\n")
        
        # Output strength development
        f.write("\nStrength Development (MPa):\n")
        f.write("Time(days) | Compressive | Flexural | Tensile\n")
        f.write("-" * 50 + "\n")
        for i, time in enumerate(time_days_list):
            strength = strengths[i]
            f.write(f"{time:6.1f} | {strength['compressive']:10.2f} | {strength['flexural']:7.2f} | {strength['tensile']:6.2f}\n")
        
        # Output hydration products
        f.write("\n28-day Hydration Products (mol):\n")
        day28_index = time_days_list.index(28)
        products = results['hydration_products'][day28_index]
        for product, amount in products.items():
            f.write(f"{product}: {amount:.2f} mol\n")
        
        f.write("\nSimulation completed! Results saved to 'cement_hydration_results.png'\n")
    
    # Generate 2D and 3D particle packing visualization
    concrete_simulator = ConcreteSimulator()
    
    # Add materials based on mix design
    concrete_simulator.add_material('Water', 1000, 0.0001, mix_design.get('Water', 0))
    concrete_simulator.add_material('Cement', 3150, 0.00005, mix_design.get('Cement', 0))
    concrete_simulator.add_material('Fly Ash', 2400, 0.00004, mix_design.get('Fly Ash', 0))
    concrete_simulator.add_material('Slag', 2900, 0.00006, mix_design.get('Slag', 0))
    concrete_simulator.add_material('Sand', 2650, 0.0005, mix_design.get('Sand', 0))
    concrete_simulator.add_material('Aggregate', 2700, 0.005, mix_design.get('Aggregate', 0))
    concrete_simulator.add_material('Steel Fiber', 7850, 0.0001, mix_design.get('Steel Fiber', 0))
    
    # Run simulation and generate visualizations
    concrete_simulator.run_simulation()
    concrete_simulator.visualize_2d()
    concrete_simulator.visualize_3d()
    
    print("Results written to hydration_results.txt and cement_hydration_results.png")

def test_composite_cements():
    """Test composite cement systems"""
    print("Testing composite cement systems...")
    
    # Test 1: Portland + Sulphoaluminate cement
    print("\nTest 1: Portland + Sulphoaluminate cement (50:50 blend)")
    try:
        simulator1 = CementHydration('portland_sulphoaluminate', {
            'portland': 0.5,
            'sulphoaluminate': 0.5
        })
        print("OK: Successfully created Portland + Sulphoaluminate cement simulator")
        print(f"  Clinker composition: {simulator1.clinker_composition}")
        
        # Test hydration degree calculation
        degrees1 = simulator1.calculate_hydration_degree(1)
        print(f"  Hydration degrees at 1 day: {degrees1}")
        
        # Test heat generation
        heat1 = simulator1.calculate_heat_generation(300, degrees1)
        print(f"  Heat generation at 1 day: {heat1:.2f} kJ")
        
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: Portland + Sulphoaluminate + Gypsum cement
    print("\nTest 2: Portland + Sulphoaluminate + Gypsum cement (40:40:20 blend)")
    try:
        simulator2 = CementHydration('portland_sulphoaluminate_gypsum', {
            'portland': 0.4,
            'sulphoaluminate': 0.4,
            'gypsum': 0.2
        })
        print("OK: Successfully created Portland + Sulphoaluminate + Gypsum cement simulator")
        print(f"  Clinker composition: {simulator2.clinker_composition}")
        
        # Test hydration degree calculation
        degrees2 = simulator2.calculate_hydration_degree(1)
        print(f"  Hydration degrees at 1 day: {degrees2}")
        
        # Test heat generation
        heat2 = simulator2.calculate_heat_generation(300, degrees2)
        print(f"  Heat generation at 1 day: {heat2:.2f} kJ")
        
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\nTesting completed!")

def test_extensions():
    """Test extension modules"""
    print("Testing extension modules...")
    
    # Test chloride diffusion
    print("\nTest 1: Chloride Diffusion Coefficient Calculation")
    simulator = CementHydration()
    depth_mm = [0, 5, 10, 15, 20, 25, 30]
    concentration = [1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05]
    time_days = 90
    diffusion_results = simulator.calculate_chloride_diffusion(depth_mm, concentration, time_days)
    if diffusion_results:
        print(f"  Diffusion coefficient: {diffusion_results['D']:.3e} m²/s")
        print(f"  Surface chloride concentration: {diffusion_results['C0']:.3f}")
        print(f"  Diffusion depth: {diffusion_results['z0']:.3e} m")
        print("  Concentration profile plot saved as 'concentration_profile.png'")
    
    # Test machine learning strength prediction
    print("\nTest 2: Machine Learning Strength Prediction")
    ml_results = simulator.predict_strength_ml()
    for model_name, strength in ml_results.items():
        if strength is not None:
            print(f"  {model_name}: {strength:.2f} MPa")
    
    print("\nExtension modules test completed!")

if __name__ == "__main__":
    # Run composite cement tests
    test_composite_cements()
    # Run extension tests
    test_extensions()
    # Run main function
    main()
