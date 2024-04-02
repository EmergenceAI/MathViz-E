#!/bin/bash -xe

python -m src.main_tests \
--input_folder tests/single_turn \
--output_folder tests/output/single_turn \
--test_files \
graph_circle_tangents.csv \
graph_parabola_tangents.csv \
graph_circles_2.csv \
graph_circles.csv \
graph_lines_2.csv \
graph_lines.csv \
graph_polynomials.csv \
graph_quad_eqns.csv \
intercepts.csv \
intersections_of_lines.csv \
inverse_functions.csv \
linear_and_nonlinear_functions.csv \
linear_equation_systems.csv \
linear_inequalities_2.csv \
linear_inequalities.csv \
local_optima.csv \
proportional_relationships.csv \
rigid_transformations.csv \
transform_shapes.csv \
transformations_of_functions_2.csv \
transformations_of_functions.csv