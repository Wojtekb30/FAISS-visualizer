extends CharacterBody3D

var speed = 0.5
var mouse_sensitivity = 0.002

@onready var head = $Camera3D
@onready var main_node = $".." # Reference to the Main scene root
@onready var info_window = $"../UI/InfoWindow"
@onready var info_text = $"../UI/InfoWindow/MarginContainer/ScrollContainer/VBoxContainer/InfoText"
@onready var info_meta = $"../UI/InfoWindow/MarginContainer/ScrollContainer/VBoxContainer/InfoMeta"
@onready var close_button = $"../UI/InfoWindow/MarginContainer/ScrollContainer/VBoxContainer/CloseButton"
func _ready():
	#Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	close_button.pressed.connect(_on_close_button_pressed)

func _input(event):
	# Mouse Look
	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sensitivity)
		head.rotate_x(-event.relative.y * mouse_sensitivity)
		head.rotation.x = clamp(head.rotation.x, deg_to_rad(-89), deg_to_rad(89))
	
	# Reading logic: Press ENTER to select the block you are looking at
	if event is InputEventKey and (event.keycode == KEY_ENTER or event.keycode == KEY_TAB) and event.pressed and not event.echo:
		if Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
			# Shoot a mathematical ray straight out from the center of the camera
			var ray_origin = head.global_position
			var ray_dir = -head.global_transform.basis.z
			
			var hit_data = main_node.get_pointed_data(ray_origin, ray_dir)
			if hit_data != null:
				show_info(hit_data)

	# Left click simply recaptures the mouse if you freed it (and the UI is closed)
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		if Input.get_mouse_mode() == Input.MOUSE_MODE_VISIBLE and not info_window.visible:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

	# Press Escape to free mouse
	if event.is_action_pressed("ui_cancel"):
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func _physics_process(_delta):
	# WASD Movement manually mapped for reliability
	var input_dir = Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_D): input_dir.x += 1
	if Input.is_physical_key_pressed(KEY_A): input_dir.x -= 1
	if Input.is_physical_key_pressed(KEY_S): input_dir.y += 1
	if Input.is_physical_key_pressed(KEY_W): input_dir.y -= 1
	input_dir = input_dir.normalized()
	
	# Use the 'head' (Camera) basis so we fly directly where we are looking
	var direction = (head.global_transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	# Q and E for straight vertical elevation
	var vertical = 0.0
	if Input.is_physical_key_pressed(KEY_E): vertical += 1.0
	if Input.is_physical_key_pressed(KEY_Q): vertical -= 1.0
	
	# Add verticality to our fly direction
	direction += Vector3(0, vertical, 0)
	direction = direction.normalized()

	if direction:
		velocity = direction * speed
	else:
		velocity = Vector3.ZERO

	move_and_slide()

func show_info(data):
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	
	# 1. Display text safely
	info_text.text = data.get("text", "No text available for this point.")
	
	# 2. Display metadata safely (if available)
	var meta = data.get("meta", {})
	if meta == null or meta.is_empty():
		info_meta.text = "No metadata available."
	else:
		info_meta.text = JSON.stringify(meta, "\t")
	
	info_window.show()

func _on_close_button_pressed():
	info_window.hide()
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
