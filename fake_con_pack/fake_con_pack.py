import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D

def calculate_porosity(particle_radii, container_volume):
    total_particle_volume = np.sum((4/3) * np.pi * particle_radii**3)
    porosity = 1 - total_particle_volume / container_volume
    return max(0, porosity)  # Ensure porosity is not negative

# Parameters
container_width = 0.1
container_height = 0.1
container_depth = 0.1
container_volume = container_width * container_height * container_depth

# Predefined raw materials and corresponding material types with size ranges
raw_materials = {
    'aggregate': (5e-3, 25e-3),
    'sand': (0.5e-3, 5e-3),
    'cement': (0.001e-3, 0.15e-3),
    'fly ash': (0.0001e-3, 0.1e-3),
    'slag': (0.001e-3, 0.15e-3),
    'silica fume': (1e-7, 1e-6)
}

# Default densities for raw materials
default_densities = {
    'aggregate': 2.6,
    'sand': 2.6,
    'cement': 3.1,
    'fly ash': 2.8,
    'slag': 3.0,
    'silica fume': 2.2
}

# User input for material types and weights
material_types = []
material_weights = []
material_densities = []

print("Enter the material types and weights (press Enter after each input):")
for material_type in raw_materials:
    weight = float(input(f"Weight of {material_type} (kg): "))
    material_types.append(material_type)
    material_weights.append(weight)
    density = input(f"Enter density for {material_type} (default: {default_densities[material_type]}): ")
    if density:
        material_densities.append(float(density))
    else:
        material_densities.append(default_densities[material_type])

# User input for water volume
water_volume = float(input("Enter the water volume, less than 0.001 m^3: "))
total_packable_volume = container_volume - water_volume

# Check if material densities are provided
if not material_densities:
    print("Error: No material densities provided. Please enter at least one density.")
    exit()

# Calculate total material weight
total_material_weight = sum(material_weights)

# Calculate the number of particles based on material weight
total_particle_volume = total_material_weight / sum(density for density in material_densities)
num_particles = int(total_particle_volume / ((4/3) * np.pi * (0.5e-3)**3))
if num_particles > 10000:
    print("Number of particles is too large. Divide by 1E6 to compute fast just at this time.")
    num_particles = int(num_particles / 1E6)

# Generate particle radii based on types
particle_radii = np.array([])
for _ in range(num_particles):
    material_idx = _ % len(material_types)
    min_radius, max_radius = raw_materials[material_types[material_idx]]
    particle_radii = np.append(particle_radii, np.random.uniform(min_radius, max_radius))

# Randomly distribute particles in the container
particle_positions = np.random.uniform(0, [container_width, container_height, container_depth], size=(num_particles, 3))

# Calculate porosity
porosity = calculate_porosity(particle_radii, container_volume)
if porosity < 0:
    print("Warning: Negative porosity calculated. Please review your inputs.")
    porosity = 0  # Set porosity to 0 if negative

print(f'Porosity: {porosity:.10f}')

# Calculate density based on user-defined material densities
total_particle_mass = sum(density * total_particle_volume for density in material_densities)
m_density = (total_particle_mass + water_volume) / container_volume
print(f'Density: {m_density:.10f}')

# Calculate tortuosity
start_point = np.array([0, 0, 0])
end_point = np.array([container_width, container_height, container_depth])
actual_path_length = np.linalg.norm(particle_positions - start_point, axis=1).sum() + np.linalg.norm(end_point - particle_positions, axis=1).sum()
straight_line_distance = np.linalg.norm(end_point - start_point)
tortuosity = actual_path_length / straight_line_distance
print(f'Tortuosity: {tortuosity:.2f}')

# Define colors based on the number of material types
colors = ['r', 'g', 'b', 'm', 'c', 'y']  # Additional colors if needed

# Plot the particles with colors based on types (excluding water)
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='3d')
for i in range(num_particles):
    material_idx = i % len(material_types)
    ax.scatter(particle_positions[i, 0], particle_positions[i, 1], particle_positions[i, 2], s=particle_radii[i]*10000, c=colors[material_idx])
ax.set_xlim([0, container_width])
ax.set_ylim([0, container_height])
ax.set_zlim([0, container_depth])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.title('Fake Concrete Pack')
plt.savefig('fake_con_pack.png')
#plt.show()

# Append water input value to the material inputs
material_types.append('water')
material_weights.append(water_volume)
material_densities.append(1.0)  # Assume water density as 1.0 kg/m^3

# Save user inputs and particle distribution data to Excel file
df_user_inputs = pd.DataFrame({
    'Material Type': material_types,
    'Weight (kg)': material_weights,
    'Density': material_densities
})

df_calculated_values = pd.DataFrame({
    'Calculated Property': ['Porosity', 'Density', 'Tortuosity'],
    'Value': [porosity, m_density, tortuosity]
})

df_particle_distribution = pd.DataFrame({
    'Particle Diameter (mm)': np.sort(particle_radii * 1000)[::-1],
    'Particle Number': range(1, len(particle_radii) + 1)
})

with pd.ExcelWriter('inputs_particle_distr.xlsx') as writer:
    df_user_inputs.to_excel(writer, sheet_name='User Inputs', index=False)
    df_calculated_values.to_excel(writer, sheet_name='Calculated Values', index=False)
    df_particle_distribution.to_excel(writer, sheet_name='Particle_Distr_All_Material', index=False)

    for material_type in raw_materials:
        idx = material_types.index(material_type)
        material_particle_radii = particle_radii[idx::len(material_types)]
        df_material_particle_distribution = pd.DataFrame({
            'Particle Diameter (mm)': np.sort(material_particle_radii * 1000)[::-1],
            'Particle Number': range(1, len(material_particle_radii) + 1)
        })
        df_material_particle_distribution.to_excel(writer, sheet_name=f'Particle_Distr_{material_type}', index=False)

# Plot the whole particle distribution
plt.figure(figsize=(10, 6))
plt.plot(np.sort(particle_radii * 1000), range(1, num_particles + 1))
plt.xlabel('Particle Diameter (mm)')
plt.ylabel('Particle Number')
plt.title('Total Particle Distribution')
plt.savefig('total_particle_distr.png')
plt.show()
