#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sulphoaluminate cement hydration simulation
"""

import numpy as np
from .base import CementHydrationBase

class SulphoaluminateCement(CementHydrationBase):
    def __init__(self):
        """Initialize sulphoaluminate cement hydration simulator"""
        super().__init__('sulphoaluminate')
        
        # Cement clinker mineral composition (mass fraction)
        self.clinker_composition = {
            'C4A3S': 0.70,   # Tricalcium sulfoaluminate
            'C2S': 0.15,     # Dicalcium silicate
            'C4AF': 0.10,    # Tetracalcium aluminoferrite
            'CaSO4': 0.05    # Calcium sulfate anhydrite (Anhydrous gypsum)
        }
    
    def calculate_hydration_degree(self, time_days, temperature=20, w_c=0.5, nano_materials=None, chemical_admixtures=None):
        """Calculate hydration degree of different minerals for sulphoaluminate cement"""
        degrees = {}
        
        # Temperature factor (Arrhenius equation)
        Ea = {
            'C4A3S': 20000,  # Activation energy in J/mol (lower than Portland for faster hydration)
            'C2S': 40000,
            'C4AF': 25000,
            'CaSO4': 18000  # Activation energy for anhydrous gypsum (higher than dihydrate)
        }
        
        R = 8.314  # Gas constant in J/(mol·K)
        T_ref = 293.15  # Reference temperature (20°C) in K
        T = 273.15 + temperature  # Current temperature in K
        
        # Water availability factor
        water_factor = min(1.0, w_c / 0.45)  # Assume 0.45 is minimum w/c for full hydration
        
        # Calculate nano materials effect factor
        nano_factor = 1.0
        if nano_materials:
            for nano, mass in nano_materials.items():
                if nano in self.nano_effects and mass > 0:
                    effect = self.nano_effects[nano].get('hydration_acceleration', 1.0)
                    nano_factor *= effect ** (mass / 10)  # Normalize by 10kg/m³
        
        # Limit nano factor
        nano_factor = min(nano_factor, 2.5)
        
        # Calculate chemical admixtures effect factors
        chemical_factor = 1.0
        c3a_factor = 1.0  # Also applies to C4A3S
        
        if chemical_admixtures:
            for admixture, mass in chemical_admixtures.items():
                if admixture in self.chemical_admixtures_effects and mass > 0:
                    effects = self.chemical_admixtures_effects[admixture]
                    
                    # Hydration acceleration/retardation
                    if 'hydration_acceleration' in effects:
                        chemical_factor *= effects['hydration_acceleration'] ** (mass / 1)
                    if 'hydration_retardation' in effects:
                        chemical_factor *= effects['hydration_retardation'] ** (mass / 0.1)
                    
                    # C3A specific effects (also applies to C4A3S)
                    if 'c3a_acceleration' in effects:
                        c3a_factor *= effects['c3a_acceleration'] ** (mass / 1)
                    if 'c3a_modification' in effects:
                        c3a_factor *= effects['c3a_modification'] ** (mass / 1)
        
        # Limit chemical factors
        chemical_factor = min(chemical_factor, 3.0)
        chemical_factor = max(chemical_factor, 0.3)
        c3a_factor = min(c3a_factor, 3.0)

        # C4A3S hydration kinetics - very fast initial hydration
        temp_factor_c4a3s = np.exp(-Ea['C4A3S']/R * (1/T - 1/T_ref))
        if time_days < 0.2:
            # Rapid initial hydration
            alpha_c4a3s = 1 - np.exp(-20.0 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * time_days)
        elif time_days < 1:
            # Accelerating stage
            alpha_c4a3s = 0.6 + 0.3 * (1 - np.exp(-5.0 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * (time_days - 0.2)))
        else:
            # Decelerating stage
            alpha_c4a3s = 0.9 + 0.05 * (1 - np.exp(-0.5 * temp_factor_c4a3s * nano_factor * chemical_factor * c3a_factor * (time_days - 1)))
        degrees['C4A3S'] = min(alpha_c4a3s * water_factor, 0.95)
        
        # C2S hydration kinetics - similar to Portland but slower relative to C4A3S
        temp_factor_c2s = np.exp(-Ea['C2S']/R * (1/T - 1/T_ref))
        alpha_c2s = 1 - np.exp(-0.2 * temp_factor_c2s * nano_factor * chemical_factor * time_days**0.7)
        degrees['C2S'] = min(alpha_c2s * water_factor, 0.85)
        
        # C4AF hydration kinetics
        temp_factor_c4af = np.exp(-Ea['C4AF']/R * (1/T - 1/T_ref))
        if time_days < 0.5:
            # Initial hydration
            alpha_c4af = 1 - np.exp(-10.0 * temp_factor_c4af * nano_factor * chemical_factor * time_days)
        else:
            # Slower hydration
            alpha_c4af = 0.7 + 0.2 * (1 - np.exp(-0.3 * temp_factor_c4af * nano_factor * chemical_factor * (time_days - 0.5)))
        degrees['C4AF'] = min(alpha_c4af * water_factor, 0.90)
        
        # CaSO4 anhydrite hydration kinetics - slower than dihydrate gypsum
        temp_factor_caso4 = np.exp(-Ea['CaSO4']/R * (1/T - 1/T_ref))
        alpha_caso4 = 1 - np.exp(-4.0 * temp_factor_caso4 * nano_factor * chemical_factor * time_days)
        degrees['CaSO4'] = min(alpha_caso4 * water_factor, 0.99)
        
        return degrees
    
    def calculate_hydration_products(self, cement_mass, hydration_degrees, fly_ash_mass=0, slag_mass=0, time_days=0, temperature=20, w_c=0.5):
        """Calculate hydration products for sulphoaluminate cement"""
        # Calculate mass of each mineral in cement
        mineral_mass = {}
        for mineral, fraction in self.clinker_composition.items():
            mineral_mass[mineral] = cement_mass * fraction
        
        # Calculate moles of each mineral
        mineral_moles = {}
        for mineral, mass in mineral_mass.items():
            mineral_moles[mineral] = mass * 1000 / self.molar_mass[mineral]  # Convert to grams, then calculate moles
        
        # Calculate hydration products
        products = {
            'CSH': 0,              # Calcium silicate hydrate
            'CASH': 0,             # Calcium aluminate silicate hydrate
            'CH': 0,               # Calcium hydroxide
            'ettringite': 0,        # Ettringite
            'ettringite_sulpho': 0, # Ettringite from sulphoaluminate hydration
            'monosulphate': 0,      # Monosulphate
            'C3AH6': 0,            # C3AH6 (hydrogarnet)
            'C4AH13': 0,           # C4AH13
            'straetlingite': 0,      # Straetlingite
            'Fe-ettringite': 0,      # Fe-ettringite
            'hydrotalcite': 0,       # Hydrotalcite (HT)
            'AlOH': 0,             # Aluminum hydroxide
            'SiOH': 0,              # Silica gel
            'thaumasite': 0,         # Thaumasite
            'CAH10': 0,             # Calcium aluminate hydrate (CAH10)
            'C2AH8': 0,             # Calcium aluminate hydrate (C2AH8)
            'AH3': 0,               # Aluminum hydroxide (Gibbsite)
            'MCPM': 0,              # Magnesium potassium phosphate hexahydrate
            'MgO': 0,               # Magnesium oxide (unreacted)
            'KH2PO4': 0             # Potassium dihydrogen phosphate (unreacted)
        }
        
        # C4A3S hydration: C4A3S + 8CaSO4 + 64H2O → 3Ca6Al2(SO4)3(OH)12·26H2O (ettringite)
        if 'C4A3S' in mineral_moles and 'C4A3S' in hydration_degrees:
            c4a3s_moles = mineral_moles['C4A3S'] * hydration_degrees['C4A3S']
            products['ettringite_sulpho'] += c4a3s_moles * 3
        
        # C2S hydration: C2S + 3.3H2O → C0.8333SH1.3333 (tobermorite-type) + CH
        if 'C2S' in mineral_moles and 'C2S' in hydration_degrees:
            c2s_moles = mineral_moles['C2S'] * hydration_degrees['C2S']
            products['CSH'] += c2s_moles * 0.5
            products['CH'] += c2s_moles
        
        # C4AF hydration: Forms Fe-ettringite
        if 'C4AF' in mineral_moles and 'C4AF' in hydration_degrees:
            c4af_moles = mineral_moles['C4AF'] * hydration_degrees['C4AF']
            products['Fe-ettringite'] += c4af_moles
        
        # CaSO4 hydration: Reacts with C4A3S to form ettringite
        if 'CaSO4' in mineral_moles and 'CaSO4' in hydration_degrees:
            caso4_moles = mineral_moles['CaSO4'] * hydration_degrees['CaSO4']
            # Already accounted for in C4A3S reaction
        
        # Slag hydration (similar to Portland)
        if slag_mass > 0:
            # Slag reactivity depends on time, temperature, and w/c ratio
            slag_reactivity = 0.34 * (1 - np.exp(-0.005 * time_days))
            # Temperature effect on slag reactivity
            T_ref = 293.15  # Reference temperature (20°C) in K
            T = 273.15 + temperature  # Current temperature in K
            temp_factor_slag = np.exp(-40000/8.314 * (1/T - 1/T_ref))
            slag_reactivity *= temp_factor_slag
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)
            slag_reactivity *= water_factor
            # Limit maximum reactivity
            slag_reactivity = min(slag_reactivity, 0.34)
            
            # Slag composition (typical blast furnace slag)
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
            slag_ratio = slag_mass / (cement_mass + slag_mass)
            c_s_ratio = 1.8 - 0.8 * slag_ratio
            a_s_ratio = 0.1 + 0.2 * slag_ratio
            
            # Calculate CH consumption by slag
            ch_consumption = reacted_slag_moles * (1 - c_s_ratio)
            products['CH'] = max(0, products['CH'] - ch_consumption)
            
            # Form C-A-S-H from slag
            products['CASH'] += reacted_slag_moles
            
            # Form hydrotalcite (HT) from MgO in slag
            products['hydrotalcite'] += reacted_slag_moles * slag_composition['MgO']
        
        # Fly ash hydration (similar to Portland)
        if fly_ash_mass > 0:
            # Fly ash reactivity depends on time, temperature, and w/c ratio
            fly_ash_reactivity = 0.25 * (1 - np.exp(-0.002 * time_days))
            # Temperature effect on fly ash reactivity
            T_ref = 293.15  # Reference temperature (20°C) in K
            T = 273.15 + temperature  # Current temperature in K
            temp_factor_fly_ash = np.exp(-60000/8.314 * (1/T - 1/T_ref))
            fly_ash_reactivity *= temp_factor_fly_ash
            # Water availability effect
            water_factor = min(1.0, w_c / 0.45)
            fly_ash_reactivity *= water_factor
            # Limit maximum reactivity
            fly_ash_reactivity = min(fly_ash_reactivity, 0.25)
            
            # Fly ash composition (typical Class F fly ash)
            fly_ash_composition = {
                'SiO2': 0.55,   # 55%
                'Al2O3': 0.25,  # 25%
                'Fe2O3': 0.10,  # 10%
                'CaO': 0.05,    # 5%
                'MgO': 0.02,    # 2%
                'SO3': 0.01,    # 1%
                'Others': 0.02  # 2%
            }
            
            # Calculate fly ash moles
            fly_ash_molar_mass = 0
            for oxide, fraction in fly_ash_composition.items():
                if oxide == 'SiO2':
                    fly_ash_molar_mass += fraction * 60.08
                elif oxide == 'Al2O3':
                    fly_ash_molar_mass += fraction * 101.96
                elif oxide == 'Fe2O3':
                    fly_ash_molar_mass += fraction * 159.69
                elif oxide == 'CaO':
                    fly_ash_molar_mass += fraction * 56.08
                elif oxide == 'MgO':
                    fly_ash_molar_mass += fraction * 40.31
                elif oxide == 'SO3':
                    fly_ash_molar_mass += fraction * 80.07
            
            fly_ash_moles = fly_ash_mass * 1000 / fly_ash_molar_mass
            reacted_fly_ash_moles = fly_ash_moles * fly_ash_reactivity
            
            # Fly ash hydration consumes CH and forms C-A-S-H
            fly_ash_ratio = fly_ash_mass / (cement_mass + fly_ash_mass)
            c_s_ratio = 1.6 - 0.6 * fly_ash_ratio
            a_s_ratio = 0.15 + 0.15 * fly_ash_ratio
            
            # Calculate CH consumption by fly ash
            ch_consumption = reacted_fly_ash_moles * (1 - c_s_ratio)
            products['CH'] = max(0, products['CH'] - ch_consumption)
            
            # Form C-A-S-H from fly ash
            products['CASH'] += reacted_fly_ash_moles
        
        return products
    
    def calculate_strength(self, time_days):
        """Calculate concrete strength development for sulphoaluminate cement"""
        if time_days <= 0:
            return 0
        
        # Strength development model for sulphoaluminate cement
        # Fast early strength, slower later development
        strength = 35 * (1 - np.exp(-1.5 * time_days**0.7)) + 5 * (1 - np.exp(-0.1 * time_days))
        return strength
