#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portland cement hydration simulation
"""

import numpy as np
from .base import CementHydrationBase

class PortlandCement(CementHydrationBase):
    def __init__(self):
        """Initialize Portland cement hydration simulator"""
        super().__init__('portland')
        
        # Cement clinker mineral composition (mass fraction)
        self.clinker_composition = {
            'C3S': 0.65,   # Tricalcium silicate
            'C2S': 0.15,   # Dicalcium silicate
            'C3A': 0.10,   # Tricalcium aluminate
            'C4AF': 0.10   # Tetracalcium aluminoferrite
        }
    
    def calculate_hydration_degree(self, time_days, temperature=20, w_c=0.5, nano_materials=None, chemical_admixtures=None):
        """Calculate hydration degree of different minerals based on GEMS3K-inspired kinetics"""
        degrees = {}
        
        # Activation energies in J/mol (based on CEMDATA18)
        Ea = {
            'C3S': 30000,
            'C2S': 40000,
            'C3A': 25000,
            'C4AF': 28000
        }
        
        # Rate constants at reference temperature (mol/m2/s)
        rate_constants = {
            'C3S': 1.0e-5,
            'C2S': 2.0e-6,
            'C3A': 5.0e-5,
            'C4AF': 8.0e-6
        }
        
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

        # Initial surface area (m2/kg)
        initial_surface_area = {
            'C3S': 300,
            'C2S': 250,
            'C3A': 400,
            'C4AF': 350
        }

        # Calculate hydration degrees using GEMS3K-inspired kinetics
        for mineral in ['C3S', 'C2S', 'C3A', 'C4AF']:
            # Calculate Arrhenius factor
            arrhenius_factor = self.calculate_arrhenius_factor(Ea[mineral], temperature)
            
            # Calculate surface area factor (varies with hydration degree)
            # Using a simplified approach since we don't have full particle size distribution
            surface_area_factor = 1.0
            
            # Calculate catalytic term (including nano and chemical effects)
            catalytic_term = nano_factor * chemical_factor
            if mineral in ['C3A', 'C4AF']:
                catalytic_term *= c3a_factor
            
            # Calculate saturation index (simplified)
            saturation_index = 0.8  # Typical value for dissolution
            
            # Calculate affinity term
            affinity_term = self.calculate_affinity_term(saturation_index)
            
            # Calculate reaction rate
            rate = self.calculate_reaction_rate(
                rate_constants[mineral],
                arrhenius_factor,
                catalytic_term,
                affinity_term
            )
            
            # Convert rate to hydration degree using integrated rate equation
            # Assuming first-order kinetics with surface area dependence
            k = rate * initial_surface_area[mineral] * 1000  # Convert to 1/day
            
            # Three-stage hydration model
            if mineral == 'C3S':
                if time_days < 1:
                    # Initial stage - rapid dissolution
                    alpha = 1 - np.exp(-5.0 * k * time_days)
                elif time_days < 14:
                    # Accelerating stage - CSH nucleation and growth
                    alpha = 0.3 + 0.4 * (1 - np.exp(-0.8 * k * (time_days - 1)))
                else:
                    # Decelerating stage - diffusion controlled
                    alpha = 0.7 + 0.2 * (1 - np.exp(-0.1 * k * (time_days - 14)))
                max_alpha = 0.95
            
            elif mineral == 'C2S':
                # Slower, more gradual hydration
                alpha = 1 - np.exp(-0.3 * k * time_days**0.7)
                max_alpha = 0.85
            
            elif mineral == 'C3A':
                # Very fast initial, then slows
                if time_days < 0.5:
                    alpha = 1 - np.exp(-15.0 * k * time_days)
                else:
                    alpha = 0.6 + 0.3 * (1 - np.exp(-0.3 * k * (time_days - 0.5)))
                max_alpha = 0.98
            
            elif mineral == 'C4AF':
                # Moderate initial hydration
                if time_days < 1:
                    alpha = 1 - np.exp(-4.0 * k * time_days)
                else:
                    alpha = 0.4 + 0.4 * (1 - np.exp(-0.4 * k * (time_days - 1)))
                max_alpha = 0.90
            
            degrees[mineral] = min(alpha * water_factor, max_alpha)
        
        return degrees
    
    def calculate_hydration_products(self, cement_mass, hydration_degrees, fly_ash_mass=0, slag_mass=0, time_days=0, temperature=20, w_c=0.5):
        """Calculate hydration products based on CEMDATA18 reactions"""
        # Calculate mass of each mineral in cement
        mineral_mass = {}
        for mineral, fraction in self.clinker_composition.items():
            mineral_mass[mineral] = cement_mass * fraction
        
        # Calculate moles of each mineral
        mineral_moles = {}
        for mineral, mass in mineral_mass.items():
            mineral_moles[mineral] = mass * 1000 / self.molar_mass[mineral]  # Convert to grams, then calculate moles
        
        # Calculate hydration products based on CEMDATA18 reactions
        products = {
            'CSH': 0,              # Calcium silicate hydrate
            'CASH': 0,             # Calcium aluminate silicate hydrate
            'CH': 0,               # Calcium hydroxide (Portlandite)
            'ettringite': 0,        # Ettringite
            'monosulphate': 0,      # Monosulphate
            'C3AH6': 0,            # C3AH6 (hydrogarnet)
            'C4AH13': 0,           # C4AH13
            'C4AH19': 0,           # C4AH19
            'straetlingite': 0,      # Straetlingite
            'Fe-ettringite': 0,      # Fe-ettringite
            'hydrotalcite': 0,       # Hydrotalcite (HT)
            'Friedels_salt': 0,      # Friedel's salt
            'Kuzels_salt': 0,       # Kuzel's salt
            'AlOH': 0,             # Aluminum hydroxide
            'SiOH': 0,              # Silica gel
            'ettringite_sulpho': 0,  # Ettringite from sulphoaluminate hydration
            'thaumasite': 0,         # Thaumasite
            'CAH10': 0,             # Calcium aluminate hydrate (CAH10)
            'C2AH7.5': 0,           # Calcium aluminate hydrate (C2AH7.5)
            'AH3': 0,               # Aluminum hydroxide (Gibbsite)
            'MCPM': 0,              # Magnesium potassium phosphate hexahydrate
            'MgO': 0,               # Magnesium oxide (unreacted)
            'KH2PO4': 0             # Potassium dihydrogen phosphate (unreacted)
        }
        
        # Calculate C-S-H composition based on slag and fly ash content
        csh_comp = self.calculate_csh_composition(slag_mass, fly_ash_mass, cement_mass)
        csh_model = csh_comp['csh_model']
        ca_si_ratio = csh_comp['ca_si_ratio']
        
        # C3S hydration: C3S + 4.5H2O → C-S-H + CH
        # Reaction: (CaO)3SiO2 + 4.5H2O → (CaO)x(SiO2)(H2O)y + (3-x)Ca(OH)2
        if 'C3S' in mineral_moles and 'C3S' in hydration_degrees:
            c3s_moles = mineral_moles['C3S'] * hydration_degrees['C3S']
            # Calculate C-S-H and CH based on Ca/Si ratio
            csh_moles = c3s_moles
            ch_moles = c3s_moles * (3 - ca_si_ratio)
            products['CSH'] += csh_moles
            products['CH'] += ch_moles
        
        # C2S hydration: C2S + 3.3H2O → C-S-H + CH
        # Reaction: (CaO)2SiO2 + 3.3H2O → (CaO)x(SiO2)(H2O)y + (2-x)Ca(OH)2
        if 'C2S' in mineral_moles and 'C2S' in hydration_degrees:
            c2s_moles = mineral_moles['C2S'] * hydration_degrees['C2S']
            # Calculate C-S-H and CH based on Ca/Si ratio
            csh_moles = c2s_moles
            ch_moles = c2s_moles * (2 - ca_si_ratio)
            products['CSH'] += csh_moles
            products['CH'] += ch_moles
        
        # C3A hydration: Different products based on sulfate availability
        if 'C3A' in mineral_moles and 'C3A' in hydration_degrees:
            c3a_moles = mineral_moles['C3A'] * hydration_degrees['C3A']
            # Assume sufficient sulfate for ettringite formation initially
            # C3A + 3CaSO4 + 32H2O → Ca6Al2(SO4)3(OH)12·26H2O (ettringite)
            products['ettringite'] += c3a_moles * 0.6  # 60% forms ettringite
            # Remaining C3A forms monosulphate
            # C3A + CaSO4 + 12H2O → Ca4Al2(SO4)(OH)12·6H2O (monosulphate)
            products['monosulphate'] += c3a_moles * 0.3  # 30% forms monosulphate
            # Some C3A forms C4AH13
            products['C4AH13'] += c3a_moles * 0.1  # 10% forms C4AH13
        
        # C4AF hydration: Forms Fe-ettringite and Fe-monosulphate
        if 'C4AF' in mineral_moles and 'C4AF' in hydration_degrees:
            c4af_moles = mineral_moles['C4AF'] * hydration_degrees['C4AF']
            # C4AF + 3CaSO4 + 32H2O → Ca6Fe2(SO4)3(OH)12·26H2O (Fe-ettringite)
            products['Fe-ettringite'] += c4af_moles * 0.7  # 70% forms Fe-ettringite
            # Remaining forms hydrotalcite
            products['hydrotalcite'] += c4af_moles * 0.3  # 30% forms hydrotalcite
        
        # Straetlingite formation (from C3A and silica)
        # Ca2Al2SiO2(OH)10·3H2O
        if 'C3A' in mineral_moles and 'C3A' in hydration_degrees:
            c3a_moles = mineral_moles['C3A'] * hydration_degrees['C3A']
            products['straetlingite'] += c3a_moles * 0.05  # 5% of C3A forms straetlingite
        
        # Slag hydration based on Chen & Brouwers' model (Model 3) and CEMDATA18
        if slag_mass > 0:
            # Calculate slag reactivity using the new method
            slag_reactivity = self.calculate_slag_reactivity(time_days, temperature, w_c)
            
            # Calculate slag moles
            slag_molar_mass = 0
            for oxide, fraction in self.slag_composition.items():
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
            products['hydrotalcite'] += reacted_slag_moles * self.slag_composition['MgO']
        
        # Fly ash hydration (improved kinetics based on CEMDATA18)
        if fly_ash_mass > 0:
            # Calculate fly ash reactivity using the new method
            fly_ash_reactivity = self.calculate_fly_ash_reactivity(time_days, temperature, w_c)
            
            # Calculate fly ash moles
            fly_ash_molar_mass = 0
            for oxide, fraction in self.fly_ash_composition.items():
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
            # C/S ratio in C-A-S-H decreases with fly ash content
            fly_ash_ratio = fly_ash_mass / (cement_mass + fly_ash_mass)
            c_s_ratio = 1.6 - 0.6 * fly_ash_ratio  # Typical C/S ratio
            a_s_ratio = 0.15 + 0.15 * fly_ash_ratio  # Typical A/S ratio
            
            # Calculate CH consumption by fly ash
            # Fly ash reacts with CH to form C-A-S-H
            ch_consumption = reacted_fly_ash_moles * (1 - c_s_ratio)  # More accurate CH consumption
            products['CH'] = max(0, products['CH'] - ch_consumption)
            
            # Form C-A-S-H from fly ash
            products['CASH'] += reacted_fly_ash_moles
        
        # Add C4AH19 formation at early ages
        if time_days < 7 and 'C3A' in mineral_moles and 'C3A' in hydration_degrees:
            c3a_moles = mineral_moles['C3A'] * hydration_degrees['C3A']
            products['C4AH19'] += c3a_moles * 0.1  # 10% forms C4AH19 at early ages
        
        return products
    
    def calculate_strength(self, time_days):
        """Calculate concrete strength development for Portland cement"""
        if time_days <= 0:
            return 0
        
        # Strength development model for Portland cement
        # Based on typical strength development curves
        strength = 40 * (1 - np.exp(-0.5 * time_days**0.5))
        return strength
