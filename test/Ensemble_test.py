from ctypes import windll,byref,c_void_p,c_int,c_long,c_double,POINTER,ARRAY
filename = "EnsembleC.dll"
EnsembleC = windll.LoadLibrary(filename)

handles = POINTER(c_void_p)()
handle_count = c_int()
EnsembleC.EnsembleConnect(byref(handles),byref(handle_count))
assert handle_count.value == 1
handle = handles.contents
c_value = c_double()
EnsembleC.EnsembleRegisterDoubleGlobalRead(handle,c_int(0),byref(c_value))
value = c_value.value
value += 1
EnsembleC.EnsembleRegisterDoubleGlobalWrite(handle,c_int(0),c_double(value))
EnsembleC.EnsembleRegisterDoubleGlobalRead(handle,c_int(0),byref(c_value))
value = c_value.value

axis_number = 2 # 0=X,1=Y,2=Z,3=PHI
c_position = c_double()
PositionFeedback = 1
EnsembleC.EnsembleStatusGetItem(handle,c_int(axis_number),
    c_int(PositionFeedback),byref(c_position))
position = c_position.value

position += 0.001
speed = 10.0
axis_mask = (1 << axis_number)
positions = ARRAY(c_double,1)(position)
speeds = ARRAY(c_double,1)(speed)
EnsembleC.EnsembleMotionMoveAbs(handle,c_int(axis_mask),positions,speeds) 
