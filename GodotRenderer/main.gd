extends Node3D

var json_file_path = "" # Start empty
var data_points = [] 

# --- NEW VARIABLES FOR RESIZING ---
var current_cube_size: float = 0.005
var shared_box_mesh: BoxMesh
var shared_material: ShaderMaterial

func _ready():
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	
	var file_dialog = FileDialog.new()
	file_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	file_dialog.access = FileDialog.ACCESS_FILESYSTEM 
	file_dialog.add_filter("*.json", "JSON Data Files")
	file_dialog.use_native_dialog = true 
	
	file_dialog.initial_position = Window.WINDOW_INITIAL_POSITION_CENTER_MAIN_WINDOW_SCREEN
	file_dialog.size = Vector2(800, 600)
	
	add_child(file_dialog)
	
	file_dialog.file_selected.connect(_on_file_selected)
	file_dialog.canceled.connect(_on_file_canceled)
	
	file_dialog.popup()

# --- NEW MOUSE WHEEL INPUT LOGIC ---
func _input(event):
	# Only allow resizing if we are actively flying around
	if Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		if event is InputEventMouseButton and event.pressed:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				resize_cubes(1.1) # Increase size by 10%
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				resize_cubes(0.9) # Decrease size by 10%

func resize_cubes(multiplier: float):
	if shared_box_mesh == null or shared_material == null:
		return
		
	# Apply multiplier and clamp it so it doesn't get infinitely big or small
	current_cube_size *= multiplier
	current_cube_size = clamp(current_cube_size, 0.0001, 2.0)
	
	var new_size_vec = Vector3(current_cube_size, current_cube_size, current_cube_size)
	
	# 1. Update the actual 3D Mesh
	shared_box_mesh.size = new_size_vec
	# 2. Update the Shader uniform so outlines stay perfect
	shared_material.set_shader_parameter("box_size", new_size_vec)

func _on_file_canceled():
	print("File selection canceled. Quitting.")
	get_tree().quit()

func _on_file_selected(path: String):
	json_file_path = path
	load_and_spawn_data()

func load_and_spawn_data():
	var file = FileAccess.open(json_file_path, FileAccess.READ)
	if file == null:
		print("Failed to open file at path: ", json_file_path)
		return
		
	var json = JSON.new()
	var error = json.parse(file.get_as_text())
	
	if error != OK:
		print("JSON Parse Error: ", json.get_error_message())
		return
		
	var data_array = json.data
	
	var min_pos = Vector3(INF, INF, INF)
	var max_pos = Vector3(-INF, -INF, -INF)
	for item in data_array:
		var pos_arr = item.get("position_3d", [0, 0, 0])
		var pos = Vector3(pos_arr[0], pos_arr[1], pos_arr[2])
		min_pos = min_pos.min(pos)
		max_pos = max_pos.max(pos)

	var mm_instance = MultiMeshInstance3D.new()
	var multimesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true 
	multimesh.instance_count = data_array.size()
	
	# --- MODIFIED MESH AND MATERIAL SETUP ---
	shared_box_mesh = BoxMesh.new()
	shared_box_mesh.size = Vector3(current_cube_size, current_cube_size, current_cube_size) 
	
	var shader = Shader.new()
	shader.code = """
		shader_type spatial;
		render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_lambert, specular_schlick_ggx;

		uniform float outline_thickness : hint_range(0.0, 0.5) = 0.05; 
		uniform vec3 box_size = vec3(0.005, 0.005, 0.005);

		varying vec3 local_pos;
		
		void vertex() {
			local_pos = VERTEX; 
		}

		void fragment() {
			vec3 abs_pos = abs(local_pos) / (box_size / 2.0);
			vec3 dist_to_edge = vec3(1.0) - abs_pos;
			vec3 is_near_edge = step(dist_to_edge, vec3(outline_thickness));
			float edge_sum = is_near_edge.x + is_near_edge.y + is_near_edge.z;

			if (edge_sum >= 1.9) {
				ALBEDO = vec3(1.0, 1.0, 1.0); 
				EMISSION = vec3(0.8, 0.8, 0.8); 
			} else {
				ALBEDO = COLOR.rgb; 
				EMISSION = COLOR.rgb * 0.5; 
				ROUGHNESS = 1.0; 
			}
		}
	"""
	
	shared_material = ShaderMaterial.new()
	shared_material.shader = shader
	# Initialize the shader parameter explicitly
	shared_material.set_shader_parameter("box_size", Vector3(current_cube_size, current_cube_size, current_cube_size))
	shared_box_mesh.material = shared_material
	
	multimesh.mesh = shared_box_mesh
	mm_instance.multimesh = multimesh
	add_child(mm_instance)

	for i in range(data_array.size()):
		var item = data_array[i]
		var pos_arr = item.get("position_3d", [0, 0, 0])
		var pos = Vector3(pos_arr[0], pos_arr[1], pos_arr[2])
		
		var r = (pos.x - min_pos.x) / (max_pos.x - min_pos.x) if max_pos.x != min_pos.x else 0.5
		var g = (pos.y - min_pos.y) / (max_pos.y - min_pos.y) if max_pos.y != min_pos.y else 0.5
		var b = (pos.z - min_pos.z) / (max_pos.z - min_pos.z) if max_pos.z != min_pos.z else 0.5
		
		multimesh.set_instance_transform(i, Transform3D(Basis(), pos))
		multimesh.set_instance_color(i, Color(r, g, b))
		
		data_points.append({
			"pos": pos,
			"text": item.get("text", "No text"),
			"meta": item.get("metadata", {})
		})

	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

# --- MODIFIED RAYCAST FUNCTION ---
# It now automatically uses current_cube_size so you can always click them accurately!
func get_pointed_data(ray_origin: Vector3, ray_dir: Vector3):
	var closest_dist_to_cam = INF
	var hit_data = null
	var click_threshold = current_cube_size # Use the dynamic size!
	
	for data in data_points:
		var point_pos = data["pos"]
		var vector_to_point = point_pos - ray_origin
		var dot_product = vector_to_point.dot(ray_dir)
		
		if dot_product > 0:
			var projection = ray_origin + (ray_dir * dot_product)
			var distance_to_ray = point_pos.distance_to(projection)
			
			if distance_to_ray <= click_threshold:
				if dot_product < closest_dist_to_cam:
					closest_dist_to_cam = dot_product
					hit_data = data
					
	return hit_data
